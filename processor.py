import argparse
import os
import sys
from core.pdf_processor import PDFProcessor

def main():
    parser = argparse.ArgumentParser(description="Legal Document Processing System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract text and metadata")
    extract_parser.add_argument("--input", required=True, help="Input PDF file")
    extract_parser.add_argument("--output", help="Output text file")

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge multiple PDFs")
    merge_parser.add_argument("--files", nargs="+", required=True, help="Input PDF files")
    merge_parser.add_argument("--output", required=True, help="Output PDF file")

    # Redact command
    redact_parser = subparsers.add_parser("redact", help="Redact terms from PDF")
    redact_parser.add_argument("--input", required=True, help="Input PDF file")
    redact_parser.add_argument("--terms", required=True, help="File containing terms to redact (one per line)")
    redact_parser.add_argument("--output", required=True, help="Output PDF file")
    redact_parser.add_argument("--log", help="Output redaction log (CSV)")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch process a folder")
    batch_parser.add_argument("--folder", required=True, help="Input folder")
    batch_parser.add_argument("--operation", choices=["extract", "redact"], required=True, help="Operation to perform")
    batch_parser.add_argument("--terms", help="Terms file (required for redact)")
    batch_parser.add_argument("--output_folder", default="output", help="Output folder")

    args = parser.parse_args()
    processor = PDFProcessor()

    if args.command == "extract":
        print(f"Extracting from {args.input}...")
        metadata = processor.extract_metadata(args.input)
        text = processor.extract_text(args.input)
        
        print("\nMetadata:")
        for k, v in metadata.items():
            print(f"  {k}: {v}")
            
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(f"Metadata:\n{str(metadata)}\n\nText:\n{text}")
            print(f"\nExtracted content saved to {args.output}")

    elif args.command == "merge":
        print(f"Merging {len(args.files)} files into {args.output}...")
        processor.merge_pdfs(args.files, args.output)
        print("Merge complete.")

    elif args.command == "redact":
        if not os.path.exists(args.terms):
            print(f"Error: Terms file {args.terms} not found.")
            return

        with open(args.terms, "r") as f:
            terms = [line.strip() for line in f if line.strip()]

        print(f"Redacting terms from {args.input}...")
        log = processor.redact_pdf(args.input, terms, args.output)
        print(f"Redaction complete. Saved to {args.output}")

        if args.log:
            processor.export_to_csv(log, args.log)
            print(f"Redaction log saved to {args.log}")

    elif args.command == "batch":
        if not os.path.exists(args.folder):
            print(f"Error: Folder {args.folder} not found.")
            return
        
        if not os.path.exists(args.output_folder):
            os.makedirs(args.output_folder)

        files = [f for f in os.listdir(args.folder) if f.lower().endswith(".pdf")]
        print(f"Found {len(files)} PDF files in {args.folder}")

        all_logs = []
        for filename in files:
            input_path = os.path.join(args.folder, filename)
            output_path = os.path.join(args.output_folder, f"processed_{filename}")
            
            if args.operation == "extract":
                text = processor.extract_text(input_path)
                txt_output = os.path.join(args.output_folder, f"{os.path.splitext(filename)[0]}.txt")
                with open(txt_output, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Extracted {filename}")
            
            elif args.operation == "redact":
                if not args.terms:
                    print("Error: --terms required for redact operation.")
                    return
                with open(args.terms, "r") as f:
                    terms = [line.strip() for line in f if line.strip()]
                
                log = processor.redact_pdf(input_path, terms, output_path)
                all_logs.extend(log)
                print(f"Redacted {filename}")

        if all_logs:
            log_path = os.path.join(args.output_folder, "batch_redaction_log.csv")
            processor.export_to_csv(all_logs, log_path)
            print(f"Batch log saved to {log_path}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
