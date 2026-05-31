import os
import sys
import uuid
import threading
import time
import shutil
from datetime import datetime, timedelta

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
from core.pdf_processor import PDFProcessor

import logging
from logging.handlers import RotatingFileHandler

# Configure Industry-Standard Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LegalDPS')
handler = RotatingFileHandler('system.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
logger.addHandler(handler)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'uploads')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'app', 'output')
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

processor = PDFProcessor()

# Background task storage (for industry-fit async processing)
tasks = {}

def cleanup_old_files():
    """Security: Periodic cleanup of old session files (files older than 24h)."""
    while True:
        try:
            now = datetime.now()
            for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
                for session_dir in os.listdir(folder):
                    dir_path = os.path.join(folder, session_dir)
                    if os.path.isdir(dir_path):
                        mtime = datetime.fromtimestamp(os.path.getmtime(dir_path))
                        if now - mtime > timedelta(hours=24):
                            shutil.rmtree(dir_path)
        except Exception as e:
            logger.error(f"Security Cleanup Error: {e}")
        time.sleep(3600) # Run every hour

# Start cleanup thread
threading.Thread(target=cleanup_old_files, daemon=True).start()
logger.info("Security Cleanup Thread initialized.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session['session_id'])
    os.makedirs(session_upload_dir, exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_upload_dir, filename)
            file.save(file_path)
            uploaded_files.append(filename)
            
    return jsonify({"message": "Files uploaded successfully", "files": uploaded_files})

def run_async_task(task_id, session_id, operation, filenames, terms_text):
    """Worker function for asynchronous document processing."""
    logger.info(f"Task {task_id} started for session {session_id}. Operation: {operation}")
    session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    session_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    os.makedirs(session_output_dir, exist_ok=True)

    results = []
    try:
        if operation == 'extract':
            for filename in filenames:
                input_path = os.path.join(session_upload_dir, filename)
                metadata = processor.extract_metadata(input_path)
                text = processor.extract_text(input_path)
                txt_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                txt_path = os.path.join(session_output_dir, txt_filename)
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"Metadata:\n{str(metadata)}\n\nText:\n{text}")
                results.append({"original": filename, "processed": txt_filename, "type": "text"})

        elif operation == 'merge':
            input_paths = [os.path.join(session_upload_dir, f) for f in filenames]
            output_filename = f"merged_{uuid.uuid4().hex[:8]}.pdf"
            output_path = os.path.join(session_output_dir, output_filename)
            processor.merge_pdfs(input_paths, output_path)
            results.append({"original": "Multiple Files", "processed": output_filename, "type": "pdf"})

        elif operation == 'redact':
            terms = [t.strip() for t in terms_text.split('\n') if t.strip()]
            all_logs = []
            for filename in filenames:
                input_path = os.path.join(session_upload_dir, filename)
                output_filename = f"redacted_{filename}"
                output_path = os.path.join(session_output_dir, output_filename)
                log = processor.redact_pdf(input_path, terms, output_path)
                all_logs.extend(log)
                results.append({"original": filename, "processed": output_filename, "type": "pdf"})
            if all_logs:
                log_filename = f"redaction_log_{uuid.uuid4().hex[:8]}.csv"
                log_path = os.path.join(session_output_dir, log_filename)
                processor.export_to_csv(all_logs, log_path)
                results.append({"original": "Redaction Log", "processed": log_filename, "type": "csv"})

        elif operation == 'ocr':
            for filename in filenames:
                input_path = os.path.join(session_upload_dir, filename)
                output_filename = f"ocr_{filename}"
                output_path = os.path.join(session_output_dir, output_filename)
                processor.perform_ocr(input_path, output_path)
                results.append({"original": filename, "processed": output_filename, "type": "pdf"})

        tasks[task_id] = {"status": "completed", "results": results}
        logger.info(f"Task {task_id} completed successfully.")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    operation = data.get('operation')
    filenames = data.get('files', [])
    terms_text = data.get('terms', '')
    
    if not filenames:
        return jsonify({"error": "No files selected"}), 400
    if 'session_id' not in session:
        return jsonify({"error": "Session expired"}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    
    # Start background processing
    thread = threading.Thread(
        target=run_async_task, 
        args=(task_id, session['session_id'], operation, filenames, terms_text)
    )
    thread.start()
    
    return jsonify({"task_id": task_id})

@app.route('/task_status/<task_id>')
def task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route('/download/<filename>')
def download(filename):
    if 'session_id' not in session:
        return "Session expired", 400
    session_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session['session_id'])
    return send_from_directory(session_output_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
