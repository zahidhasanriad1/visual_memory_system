import base64
import mimetypes
import re
from pathlib import Path


def sanitize_filename_stem(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")

    return stem or "uploaded_file"


def guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))

    return mime_type or "application/octet-stream"


def encode_file_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def encode_image_data_url(path: Path) -> str:
    mime_type = guess_mime_type(path)
    encoded = encode_file_base64(path)

    return f"data:{mime_type};base64,{encoded}"