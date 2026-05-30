import mimetypes
from dataclasses import dataclass

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass(frozen=True)
class Detection:
    mime: str
    pipeline: str  # "ocr" | "text"
    strategy: str  # "fixed" | "recursive" | "sentence"


def detect(filename: str, content_type: str | None) -> Detection:
    """Decide pipeline + chunking strategy from MIME (the first ingestion step).

    Images -> OCR -> fixed-size chunks (OCR output is unstructured).
    PDFs / docx / rich text -> text pipeline -> recursive char splitting.
    Plain text -> text pipeline -> sentence-aware splitting.
    """
    mime = (content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream").lower()

    if mime.startswith("image/"):
        return Detection(mime, "ocr", "fixed")
    if mime == "text/plain":
        return Detection(mime, "text", "sentence")
    # PDF, docx, and any other text/* are structured -> recursive.
    return Detection(mime, "text", "recursive")
