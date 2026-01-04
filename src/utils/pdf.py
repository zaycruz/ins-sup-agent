from __future__ import annotations

from typing import cast

import fitz


def extract_pdf_text(pdf_binary: bytes) -> str:
    """Extract text content from a PDF binary.

    Args:
        pdf_binary: Raw bytes of the PDF file.

    Returns:
        Extracted text content from all pages, concatenated with page breaks.

    Raises:
        ValueError: If the PDF cannot be opened or parsed.
    """
    try:
        doc = fitz.open(stream=pdf_binary, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}") from e

    text_parts: list[str] = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = cast(str, page.get_text("text"))
        if page_text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

    doc.close()

    return "\n\n".join(text_parts)
