import io
import tempfile

import pytest

from src.rag.pdf_loader import PDFLoader


def _create_pdf_bytes(text: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def test_extract_text_from_stream():
    pdf_bytes = _create_pdf_bytes("Hello Earnings")
    stream = io.BytesIO(pdf_bytes)

    extracted = PDFLoader.extract_text(stream)

    assert "Hello Earnings" in extracted


def test_extract_text_from_path():
    pdf_bytes = _create_pdf_bytes("Path Based PDF")

    # Use delete=False to avoid Windows permission issues on reopen
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    extracted = PDFLoader.extract_text_from_path(tmp_path)

    assert "Path Based PDF" in extracted


def test_chunk_text_overlap():
    text = "0123456789" * 30  # 300 chars
    chunks = PDFLoader.chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) >= 3
    # Ensure overlap worked (chunk 1 tail equals chunk 2 head)
    assert chunks[0][-10:] in chunks[1]
