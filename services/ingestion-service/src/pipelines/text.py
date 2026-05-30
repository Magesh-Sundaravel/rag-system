from io import BytesIO

from src.detector import DOCX_MIME


def extract(data: bytes, mime: str, filename: str) -> str:
    """Extract text from documents. Lazy imports keep heavy deps off the hot path."""
    if mime == "application/pdf":
        return _from_pdf(data)
    if mime == DOCX_MIME or filename.lower().endswith(".docx"):
        return _from_docx(data)
    return data.decode("utf-8", errors="ignore")


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _from_docx(data: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(data))
    return "\n\n".join(p.text for p in document.paragraphs)
