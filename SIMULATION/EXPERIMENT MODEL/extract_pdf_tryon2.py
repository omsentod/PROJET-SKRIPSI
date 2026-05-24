import sys
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("No pypdf installed")
        sys.exit(1)

reader = PdfReader("/Users/macbook/piton/PROJECT_SKRIPSI/SIMULATION/EXPERIMENT MODEL/SKIRPSI BAB 1-3 tryon 2.pdf")
with open("/Users/macbook/piton/PROJECT_SKRIPSI/SIMULATION/EXPERIMENT MODEL/skripsi_tryon2_text.txt", "w") as f:
    for page in reader.pages:
        f.write(page.extract_text() or "")
        f.write("\n--- PAGE BREAK ---\n")
print("Done")
