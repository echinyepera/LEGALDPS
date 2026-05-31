# LegalDPS User Guide

Welcome to the Legal Document Processing System. This guide will help you get started with the application.

## 1. Getting Started
- Open the application in your web browser (usually at `http://localhost:5000`).
- You will see a dashboard with two main sections: **Upload Documents** and **Results**.

## 2. Uploading Files
- **Drag and Drop**: Simply drag your PDF files into the dashed box.
- **Browse**: Click on the dashed box to select files from your computer.
- Once uploaded, files will appear in the list below the upload area. You can remove any file by clicking the 'X' icon.

## 3. Operations
Choose one of the four available operations:

### A. Extract Text & Metadata
- Pulls all text and document information (Author, Title, Page Count).
- **Output**: A text file (`.txt`) containing the extracted data.

### B. Merge Documents
- Combines all uploaded PDFs into a single file.
- **Output**: A single merged PDF.

### C. Redact Sensitive Info
- Permanently removes specific terms from your documents.
- **How to use**: Enter terms or regular expressions in the text box (one per line).
- **Example terms**: `John Doe`, `Confidential`.
- **Example regex**: `regex:\d{3}-\d{2}-\d{4}` (for SSNs).
- **Output**: Redacted PDFs and a detailed Redaction Log (CSV).

### D. OCR (Scanned PDFs)
- Uses Optical Character Recognition to convert scanned images into searchable text.
- **Output**: A new PDF with searchable text layers.

## 4. Processing
- After selecting an operation, click **Process Documents**.
- A progress bar will show the status of the operation.
- Results will appear in the right-hand panel once finished.

## 5. Downloading Results
- Click the **Download** button next to any processed file in the results list to save it to your computer.

---
**Tip**: For redaction, always double-check the Redaction Log to ensure all intended terms were found and removed.
