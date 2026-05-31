# LegalDPS - Legal Document Processing System

LegalDPS is a Python-based system designed to automate the processing of legal documents (PDFs). It provides tools for text extraction, merging, redaction, and OCR.

## Features

- **PDF Extraction**: Pull text, metadata, and specific fields using keywords.
- **PDF Merging**: Combine multiple PDFs into a single document with preserved formatting.
- **PDF Redaction**: Permanently remove sensitive information using text matches or regular expressions.
- **OCR Support**: Process scanned or image-based PDFs to make them searchable.
- **Batch Processing**: Handle multiple files simultaneously.
- **Modern Web UI**: Easy-to-use drag-and-drop interface.
- **CLI Tool**: Command-line interface for automation and scripting.

## Installation

1. **Python 3.10+** is required.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Optional (for OCR)**: Install [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) and ensure it's in your system PATH.

## Usage

### Web Interface
Start the web application:
```bash
python app/app.py
```
Open your browser to `http://127.0.0.1:5000`.

### Command Line Interface (CLI)
The `processor.py` script provides various commands:

**Extract text:**
```bash
python processor.py extract --input document.pdf --output extracted.txt
```

**Merge PDFs:**
```bash
python processor.py merge --files doc1.pdf doc2.pdf --output merged.pdf
```

**Redact by terms:**
```bash
python processor.py redact --input document.pdf --terms terms.txt --output redacted.pdf --log redaction_log.csv
```

**Batch process folder:**
```bash
python processor.py batch --folder ./docs --operation redact --terms terms.txt
```

## Project Structure

- `app/`: Flask web application (UI and backend).
- `core/`: Core PDF processing logic using PyMuPDF.
- `processor.py`: CLI wrapper for the core logic.
- `terms.txt`: Sample redaction terms and regex patterns.
- `tests/`: Automated tests.

## Security Note
Redaction in LegalDPS is **permanent**. It uses PyMuPDF's `apply_redactions()` which removes the underlying text and images from the PDF structure, ensuring sensitive data cannot be recovered.
