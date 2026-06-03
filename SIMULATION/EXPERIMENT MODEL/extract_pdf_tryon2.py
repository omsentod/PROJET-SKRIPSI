import sys
import os

try:
    from pypdf import PdfReader
except ImportError:
    print("Error: No pypdf library installed. Run 'pip install pypdf'.")
    sys.exit(1)


# Using relative paths since this script resides in the same directory as the PDF file
pdf_path = "SKIRPSI BAB 1-3 tryon 2.pdf"
output_path = "skripsi_tryon2_text.txt"

if not os.path.exists(pdf_path):
    print(f"Error: Source PDF file not found at '{pdf_path}' in the current directory.")
    sys.exit(1)

print(f"Reading: {pdf_path}")
reader = PdfReader(pdf_path)

with open(output_path, "w", encoding="utf-8") as f:
    for page in reader.pages:
        f.write(page.extract_text() or "")
        f.write("\n--- PAGE BREAK ---\n")

print(f"Successfully extracted text to: {output_path}")

