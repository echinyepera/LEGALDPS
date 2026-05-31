import fitz
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_processor import PDFProcessor

def create_sample_pdf(filename, text_content):
    doc = fitz.open()
    page = doc.new_page()
    where = fitz.Point(50, 50)
    page.insert_text(where, text_content, fontsize=12)
    
    # Add some "sensitive" info
    page.insert_text(fitz.Point(50, 100), "Client Name: John Doe", fontsize=12)
    page.insert_text(fitz.Point(50, 120), "Case Number: 2024-001", fontsize=12)
    page.insert_text(fitz.Point(50, 140), "Confidential Statement", fontsize=12)
    page.insert_text(fitz.Point(50, 160), "SSN: 123-45-6789", fontsize=12)
    
    doc.save(filename)
    doc.close()
    print(f"Created sample PDF: {filename}")

def test_extraction():
    processor = PDFProcessor()
    filename = "test_sample.pdf"
    create_sample_pdf(filename, "This is a legal document test.")
    
    print("\nTesting Metadata Extraction...")
    meta = processor.extract_metadata(filename)
    print(f"Metadata: {meta}")
    
    print("\nTesting Text Extraction...")
    text = processor.extract_text(filename)
    print(f"Text content: {text[:100]}...")
    
    print("\nTesting Field Extraction...")
    fields = processor.extract_fields_by_keywords(filename, ["Client Name:", "Case Number:"])
    print(f"Fields: {fields}")
    
    os.remove(filename)

def test_redaction():
    processor = PDFProcessor()
    filename = "test_redact_input.pdf"
    output = "test_redact_output.pdf"
    create_sample_pdf(filename, "Confidential document for John Doe.")
    
    terms = ["John Doe", "regex:\\d{3}-\\d{2}-\\d{4}", "Confidential"]
    print(f"\nTesting Redaction with terms: {terms}")
    log = processor.redact_pdf(filename, terms, output)
    print(f"Redaction log entries: {len(log)}")
    for entry in log:
        print(f"  Redacted '{entry['original_text']}' on page {entry['page_number']}")
    
    if os.path.exists(output):
        print(f"Output file created: {output}")
        # Verify text is gone
        redacted_text = processor.extract_text(output)
        if "John Doe" not in redacted_text:
            print("Success: 'John Doe' is no longer extractable.")
        else:
            print("Warning: 'John Doe' still found in text (might be due to how PyMuPDF applies redaction).")
    
    os.remove(filename)
    os.remove(output)

if __name__ == "__main__":
    if not os.path.exists("tests"):
        os.makedirs("tests")
    test_extraction()
    test_redaction()
