from io import BytesIO


def extract(data: bytes) -> str:
    """OCR an image to raw text. Lazy imports: tesseract isn't needed to import this module."""
    import pytesseract
    from PIL import Image

    image = Image.open(BytesIO(data))
    return pytesseract.image_to_string(image)
