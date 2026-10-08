"""Screenshot OCR. EasyOCR (PyTorch) when available, else Tesseract (lite runtime)."""
import io
from functools import lru_cache

import numpy as np

from app import onnx_models

MAX_SIDE = 1600


@lru_cache(maxsize=1)
def _easyocr_reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def _load(image_bytes: bytes):
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if max(img.size) > MAX_SIDE:  # large phone screenshots are slow on CPU
        scale = MAX_SIDE / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img


def _tesseract(img) -> str:
    import pytesseract
    from PIL import ImageOps

    gray = ImageOps.grayscale(img)
    # Dark-mode screenshots (light text on dark background) OCR far better inverted.
    if np.asarray(gray).mean() < 110:
        gray = ImageOps.invert(gray)
    if max(gray.size) < 1000:  # upscale small crops
        gray = gray.resize((gray.width * 2, gray.height * 2))
    return pytesseract.image_to_string(gray)


def image_to_text(image_bytes: bytes) -> str:
    img = _load(image_bytes)
    if onnx_models.use_onnx():
        text = _tesseract(img)
    else:
        lines = _easyocr_reader().readtext(np.array(img), detail=0, paragraph=True)
        text = "\n".join(lines)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
