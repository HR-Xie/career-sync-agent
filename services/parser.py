import base64
import io
import re
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from PIL import Image


def detect_file_format(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in (".pdf", ".docx"):
        return ext.lstrip(".")

    # Magic bytes detection
    with open(file_path, "rb") as f:
        header = f.read(8)

    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"PK\x03\x04"):
        return "docx"

    raise ValueError(f"Unsupported file format: {ext or 'unknown'}")


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def clean_extracted_text(text: str) -> str:
    # Remove form feed characters
    text = text.replace("\f", "\n")
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove lines that are only whitespace
    text = re.sub(r"\n\s+\n", "\n", text)
    return text.strip()


def compress_image_to_base64(image_path: str, max_width: int = 1080) -> tuple:
    img = Image.open(image_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() == "PNG":
        img.save(buffer, format="PNG", optimize=True)
        content_type = "image/png"
    else:
        img = img.convert("RGB")
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        content_type = "image/jpeg"

    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64, content_type
