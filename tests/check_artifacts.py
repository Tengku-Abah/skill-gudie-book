"""Simple artifact verification script for CI and local pipelines."""
import sys
from pathlib import Path
try:
    import pymupdf as fitz
except ImportError:
    import fitz

def check(pdf_path: str, html_path: str):
    p_pdf = Path(pdf_path)
    p_html = Path(html_path)
    if not p_pdf.exists() or p_pdf.stat().st_size == 0:
        raise FileNotFoundError(f"PDF missing or empty: {pdf_path}")
    if not p_html.exists() or p_html.stat().st_size == 0:
        raise FileNotFoundError(f"HTML missing or empty: {html_path}")

    doc = fitz.open(str(p_pdf))
    page_count = len(doc)
    doc.close()
    if page_count < 1:
        raise ValueError(f"PDF contains 0 pages: {pdf_path}")

    html_text = p_html.read_text(encoding="utf-8")
    if "<!DOCTYPE html>" not in html_text or "slide-01.png" not in html_text:
        raise ValueError(f"HTML appears malformed or missing slide references: {html_path}")

    print(f"[OK] Artifact check passed! PDF pages: {page_count}, HTML verified.")

if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "output/guidebook.pdf"
    html_f = sys.argv[2] if len(sys.argv) > 2 else "output/index.html"
    check(pdf, html_f)
