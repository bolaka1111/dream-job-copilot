"""Resume parsing utilities supporting PDF and DOCX formats."""

from __future__ import annotations

import os
from pathlib import Path


def parse_pdf(path: str) -> str:
    """Extract plain text from a PDF file using PyPDF2."""
    try:
        import PyPDF2  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("PyPDF2 is required to parse PDF files: pip install PyPDF2") from exc

    text_parts: list[str] = []
    with open(path, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts).strip()


def parse_docx(path: str) -> str:
    """Extract plain text from a DOCX file using python-docx."""
    try:
        from docx import Document  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "python-docx is required to parse DOCX files: pip install python-docx"
        ) from exc

    doc = Document(path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs).strip()


def parse_resume(path: str) -> str:
    """Route to the correct parser based on file extension.

    Supports .pdf and .docx files.
    Raises ValueError for unsupported formats or FileNotFoundError if missing.
    """
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    ext = resolved.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(str(resolved))
    elif ext in {".docx", ".doc"}:
        return parse_docx(str(resolved))
    else:
        raise ValueError(
            f"Unsupported resume format: '{ext}'. "
            "Please provide a PDF (.pdf) or Word document (.docx)."
        )
