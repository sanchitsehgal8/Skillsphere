from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf_bytes(raw_bytes: bytes) -> str:
    """Extract plain text from a PDF byte payload."""
    if not raw_bytes:
        return ""

    reader = PdfReader(BytesIO(raw_bytes))
    pages_text: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if page_text:
            pages_text.append(page_text)

    return "\n\n".join(pages_text).strip()


def suggest_title_from_jd(text: str) -> str | None:
    """Best-effort role title guess from JD text."""
    if not text:
        return None

    first_lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:10]
    lowered = [ln.lower() for ln in first_lines]

    for line in first_lines:
        if len(line) <= 80 and any(key in line.lower() for key in ["engineer", "developer", "manager", "scientist", "architect"]):
            return line

    for i, line in enumerate(lowered):
        if "job title" in line or "role" in line:
            original = first_lines[i]
            if ":" in original:
                guess = original.split(":", 1)[1].strip()
                if guess:
                    return guess

    return None
