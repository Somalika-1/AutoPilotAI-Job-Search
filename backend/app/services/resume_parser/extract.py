from io import BytesIO

import docx
from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text(filename: str, file_bytes: bytes) -> str:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return _extract_pdf_text(file_bytes)
    if lowered.endswith(".docx"):
        return _extract_docx_text(file_bytes)
    raise UnsupportedFileTypeError(f"Unsupported file type: {filename}. Only .pdf and .docx are supported.")


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx_text(file_bytes: bytes) -> str:
    document = docx.Document(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
