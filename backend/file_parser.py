"""
file_parser.py — turns an uploaded PDF/DOCX/TXT into plain text for
ai_content.generate_diagnostic_questions().

Kept deliberately simple: one text blob, lightly trimmed to fit
comfortably in a single LLM call. No chunk-and-embed pipeline — this
app already has pgvector-free, keyword-free question storage, so a
diagnostic-only feature doesn't need one either. If uploads grow large
enough that a single call stops being enough context, chunk_text() is
the place to swap in a real chunker.
"""

import io

from pypdf import PdfReader
from docx import Document


def extract_text(filename: str, content: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == "docx":
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == "txt":
        return content.decode("utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type '.{ext}' — upload a PDF, DOCX, or TXT file.")


def chunk_text(text: str, max_chars: int = 12000) -> str:
    """Trims to something that fits comfortably in one LLM call while
    preferring to cut on a paragraph boundary instead of mid-sentence."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_break = truncated.rfind("\n\n")
    return truncated[:last_break] if last_break > max_chars * 0.5 else truncated
