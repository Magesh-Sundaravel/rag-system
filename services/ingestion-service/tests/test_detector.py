from src.detector import detect


def test_image_routes_to_ocr_fixed():
    det = detect("scan.png", "image/png")
    assert det.pipeline == "ocr"
    assert det.strategy == "fixed"


def test_pdf_routes_to_text_recursive():
    det = detect("report.pdf", "application/pdf")
    assert det.pipeline == "text"
    assert det.strategy == "recursive"


def test_plain_text_routes_to_sentence():
    det = detect("notes.txt", "text/plain")
    assert det.pipeline == "text"
    assert det.strategy == "sentence"


def test_mime_inferred_from_extension_when_missing():
    det = detect("photo.jpg", None)
    assert det.pipeline == "ocr"
