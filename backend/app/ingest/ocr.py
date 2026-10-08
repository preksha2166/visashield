"""Screenshot OCR with EasyOCR (CPU). The reader is loaded lazily on first use."""
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def image_to_text(image_bytes: bytes) -> str:
    import io

    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # Large phone screenshots are slow on CPU; cap the long side.
    max_side = 1600
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    lines = _reader().readtext(np.array(img), detail=0, paragraph=True)
    return "\n".join(line.strip() for line in lines if line.strip())
