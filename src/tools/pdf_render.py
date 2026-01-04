from __future__ import annotations

import base64
from dataclasses import dataclass

from pydantic import BaseModel, Field


class ImageEmbed(BaseModel):
    photo_id: str = Field(description="Photo identifier")
    binary: bytes = Field(description="Raw image bytes")
    caption: str = Field(description="Image caption")
    highlights: list[dict[str, float]] | None = Field(
        default=None, description="Bounding boxes to highlight"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class RenderOptions(BaseModel):
    page_size: str = Field(default="letter", description="Page size (letter, a4)")
    margin: str = Field(default="0.75in", description="Page margins")
    include_cover_page: bool = Field(default=True, description="Include cover page")
    include_photo_appendix: bool = Field(
        default=True, description="Include photo appendix"
    )
    company_name: str | None = Field(
        default=None, description="Company name for header"
    )
    company_logo_base64: str | None = Field(
        default=None, description="Base64 encoded company logo"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


@dataclass
class RenderResult:
    pdf_binary: bytes
    page_count: int
    warnings: list[str] | None = None


PRINT_CSS = """
<style>
    * {
        box-sizing: border-box;
    }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11pt;
        line-height: 1.4;
        color: #333;
        margin: 0;
        padding: 0;
    }
    h1 {
        font-size: 18pt;
        color: #1a1a1a;
        margin-bottom: 0.5em;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 0.3em;
    }
    h2 {
        font-size: 14pt;
        color: #1a1a1a;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    h3 {
        font-size: 12pt;
        color: #444;
        margin-top: 1em;
        margin-bottom: 0.3em;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        font-size: 10pt;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f8f9fa;
        font-weight: 600;
    }
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .cover-page {
        text-align: center;
        padding-top: 3in;
    }
    .cover-page h1 {
        font-size: 24pt;
        border: none;
    }
    .summary-box {
        background-color: #f0f7ff;
        border: 1px solid #2563eb;
        border-radius: 4px;
        padding: 1em;
        margin: 1em 0;
    }
    .amount {
        font-family: monospace;
        text-align: right;
    }
    .total-row {
        font-weight: bold;
        background-color: #e8f0fe !important;
    }
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1em;
        margin: 1em 0;
    }
    .photo-item {
        border: 1px solid #ddd;
        padding: 0.5em;
    }
    .photo-item img {
        max-width: 100%;
        height: auto;
    }
    .photo-caption {
        font-size: 9pt;
        color: #666;
        margin-top: 0.5em;
    }
    .page-break {
        page-break-after: always;
    }
    .footer {
        font-size: 9pt;
        color: #666;
        text-align: center;
        margin-top: 2em;
        padding-top: 1em;
        border-top: 1px solid #ddd;
    }
    @media print {
        body {
            font-size: 10pt;
        }
        .page-break {
            page-break-after: always;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        table {
            page-break-inside: avoid;
        }
        .no-print {
            display: none;
        }
    }
    @page {
        margin: 0.75in;
        size: letter;
    }
</style>
"""


class PDFRenderer:
    async def render(
        self,
        html: str,
        images: list[ImageEmbed] | None = None,
        options: RenderOptions | None = None,
    ) -> RenderResult:
        options = options or RenderOptions()
        images = images or []
        warnings: list[str] = []

        processed_html = self._embed_images(html, images)
        processed_html = self._add_print_css(processed_html, options)

        try:
            from weasyprint import HTML

            pdf_bytes = HTML(string=processed_html).write_pdf()
            page_count = self._estimate_page_count(pdf_bytes)
            return RenderResult(
                pdf_binary=pdf_bytes,
                page_count=page_count,
                warnings=warnings if warnings else None,
            )
        except ImportError:
            warnings.append("weasyprint not installed, returning HTML as placeholder")
            placeholder = f"<!-- PDF_PLACEHOLDER -->\n{processed_html}"
            return RenderResult(
                pdf_binary=placeholder.encode("utf-8"),
                page_count=1,
                warnings=warnings,
            )
        except Exception as e:
            warnings.append(f"PDF rendering failed: {e}")
            placeholder = f"<!-- PDF_ERROR: {e} -->\n{processed_html}"
            return RenderResult(
                pdf_binary=placeholder.encode("utf-8"),
                page_count=1,
                warnings=warnings,
            )

    def _embed_images(self, html: str, images: list[ImageEmbed]) -> str:
        for img in images:
            placeholder = f"{{{{IMAGE_{img.photo_id}}}}}"
            if placeholder in html:
                data_uri = self._bytes_to_data_uri(img.binary)
                html = html.replace(placeholder, data_uri)

            src_placeholder = f'src="{img.photo_id}"'
            if src_placeholder in html:
                data_uri = self._bytes_to_data_uri(img.binary)
                html = html.replace(src_placeholder, f'src="{data_uri}"')

        return html

    def _bytes_to_data_uri(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        mime = self._detect_mime_type(image_bytes)
        return f"data:{mime};base64,{b64}"

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        if image_bytes[:4] == b"\x89PNG":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        elif image_bytes[:4] == b"GIF8":
            return "image/gif"
        else:
            return "image/jpeg"

    def _add_print_css(self, html: str, options: RenderOptions) -> str:
        page_css = f"""
        @page {{
            margin: {options.margin};
            size: {options.page_size};
        }}
        """
        full_css = PRINT_CSS.replace("@page {", f"@page {{{page_css}")

        if "<head>" in html.lower():
            insert_pos = html.lower().find("<head>") + 6
            return html[:insert_pos] + full_css + html[insert_pos:]
        elif "<html>" in html.lower():
            insert_pos = html.lower().find("<html>") + 6
            return html[:insert_pos] + f"<head>{full_css}</head>" + html[insert_pos:]
        else:
            return f"<!DOCTYPE html><html><head>{full_css}</head><body>{html}</body></html>"

    def _estimate_page_count(self, pdf_bytes: bytes) -> int:
        try:
            content = pdf_bytes[:10000].decode("latin-1", errors="ignore")
            import re

            matches = re.findall(r"/Type\s*/Page[^s]", content)
            if matches:
                return len(matches)
        except Exception:
            pass
        return max(1, len(pdf_bytes) // 40000)

    def render_html_only(
        self,
        html: str,
        images: list[ImageEmbed] | None = None,
        options: RenderOptions | None = None,
    ) -> str:
        options = options or RenderOptions()
        images = images or []

        processed_html = self._embed_images(html, images)
        processed_html = self._add_print_css(processed_html, options)
        return processed_html
