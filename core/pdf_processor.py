import fitz  # PyMuPDF
import os
import re
import pandas as pd
from datetime import datetime
import pytesseract
from PIL import Image
import io

class PDFProcessor:
    def __init__(self):
        pass

    def _open_doc(self, file_path, password=None):
        """Open a PDF document with optional password handling."""
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            if password:
                if not doc.authenticate(password):
                    raise ValueError(f"Authentication failed for {os.path.basename(file_path)}")
            else:
                raise ValueError(f"Document {os.path.basename(file_path)} is password protected")
        return doc

    def extract_metadata(self, file_path, password=None):
        """Extract metadata from PDF."""
        doc = self._open_doc(file_path, password)
        metadata = doc.metadata
        page_count = doc.page_count
        doc.close()
        return {
            "author": metadata.get("author", "Unknown"),
            "creation_date": metadata.get("creationDate", "Unknown"),
            "page_count": page_count,
            "title": metadata.get("title", "Unknown"),
            "subject": metadata.get("subject", "Unknown"),
            "keywords": metadata.get("keywords", "Unknown")
        }

    def extract_text(self, file_path, password=None):
        """Extract all text from PDF."""
        doc = self._open_doc(file_path, password)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def extract_fields_by_keywords(self, file_path, keywords, password=None):
        """Extract specific fields using keywords."""
        text = self.extract_text(file_path, password)
        results = {}
        for keyword in keywords:
            # Simple regex to find text following a keyword until the end of the line
            pattern = rf"{re.escape(keyword)}\s*(.*)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                results[keyword] = match.group(1).strip()
            else:
                results[keyword] = "Not found"
        return results

    def merge_pdfs(self, file_paths, output_path, passwords=None):
        """Merge multiple PDFs into one."""
        result_doc = fitz.open()
        passwords = passwords or {}
        for path in file_paths:
            filename = os.path.basename(path)
            pwd = passwords.get(filename)
            doc = self._open_doc(path, pwd)
            result_doc.insert_pdf(doc)
            doc.close()
        result_doc.save(output_path)
        result_doc.close()
        return output_path

    def redact_pdf(self, file_path, terms, output_path, password=None):
        """
        Redact specific terms from PDF.
        Returns a log of redactions.
        """
        doc = self._open_doc(file_path, password)
        redaction_log = []
        
        for page_num, page in enumerate(doc):
            for term in terms:
                # Handle regex terms
                if term.startswith("regex:"):
                    pattern = term[6:]
                    # Find all matches for regex
                    page_text = page.get_text("text")
                    matches = re.finditer(pattern, page_text)
                    for match in matches:
                        match_text = match.group()
                        areas = page.search_for(match_text)
                        for area in areas:
                            page.add_redact_annot(area, fill=(0, 0, 0))
                            redaction_log.append({
                                "filename": os.path.basename(file_path),
                                "original_text": match_text,
                                "page_number": page_num + 1,
                                "redaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                else:
                    # Standard text search
                    areas = page.search_for(term)
                    for area in areas:
                        page.add_redact_annot(area, fill=(0, 0, 0))
                        redaction_log.append({
                            "filename": os.path.basename(file_path),
                            "original_text": term,
                            "page_number": page_num + 1,
                            "redaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            
            page.apply_redactions()
            
        doc.save(output_path)
        doc.close()
        return redaction_log

    def perform_ocr(self, file_path, output_path, password=None):
        """Perform OCR on scanned PDF and save as searchable PDF."""
        doc = self._open_doc(file_path, password)
        
        # Simple OCR implementation using pytesseract on page pixmaps
        new_doc = fitz.open()
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Higher resolution for OCR
            img = Image.open(io.BytesIO(pix.tobytes()))
            # Get OCR data
            ocr_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
            ocr_page_doc = fitz.open("pdf", ocr_pdf)
            new_doc.insert_pdf(ocr_page_doc)
            ocr_page_doc.close()
        
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path

    def export_to_csv(self, data, output_path):
        """Export data list to CSV."""
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return output_path

    def export_to_excel(self, data, output_path):
        """Export data list to Excel."""
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False)
        return output_path
