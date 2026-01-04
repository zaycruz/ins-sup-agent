from __future__ import annotations

import pytest

from src.tools.code_lookup import CodeLookupTool, CodeRequirement
from src.tools.pdf_render import PDFRenderer, ImageEmbed, RenderOptions


class TestCodeLookupTool:
    @pytest.fixture
    def tool(self) -> CodeLookupTool:
        return CodeLookupTool()

    @pytest.mark.asyncio
    async def test_lookup_by_state_code(self, tool):
        results = await tool.lookup("TX", ["ice_barrier", "drip_edge"])
        assert len(results) == 2
        assert all(isinstance(r, CodeRequirement) for r in results)

    @pytest.mark.asyncio
    async def test_lookup_by_state_name(self, tool):
        results = await tool.lookup("Texas", ["ventilation"])
        assert len(results) == 1
        assert results[0].topic == "ventilation"

    @pytest.mark.asyncio
    async def test_lookup_by_address(self, tool):
        results = await tool.lookup("123 Main St, Dallas, TX 75201", ["fastening"])
        assert len(results) == 1
        assert results[0].topic == "fastening"

    @pytest.mark.asyncio
    async def test_lookup_unknown_state(self, tool):
        results = await tool.lookup("Unknown State", ["ice_barrier"])
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_lookup_unknown_topic(self, tool):
        results = await tool.lookup("TX", ["unknown_topic"])
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_florida_codes(self, tool):
        results = await tool.lookup("FL", ["underlayment", "fastening"])
        assert len(results) == 2
        assert any(
            "hurricane" in r.requirement.lower() or "hvhz" in r.requirement.lower()
            for r in results
        )

    def test_get_all_topics(self, tool):
        topics = tool.get_all_topics()
        assert "ice_barrier" in topics
        assert "drip_edge" in topics
        assert "ventilation" in topics
        assert len(topics) == 8

    def test_get_supported_states(self, tool):
        states = tool.get_supported_states()
        assert "TX" in states
        assert "FL" in states
        assert "CA" in states
        assert len(states) == 10


class TestPDFRenderer:
    @pytest.fixture
    def renderer(self) -> PDFRenderer:
        return PDFRenderer()

    @pytest.mark.asyncio
    async def test_render_simple_html(self, renderer):
        result = await renderer.render("<html><body><h1>Test</h1></body></html>")
        assert result.pdf_binary is not None

    @pytest.mark.asyncio
    async def test_render_with_images(self, renderer):
        images = [
            ImageEmbed(
                photo_id="IMG_001",
                binary=b"\xff\xd8\xff\xe0\x00\x10JFIF",
                caption="Test photo",
            )
        ]
        html = '<html><body><img src="IMG_001"></body></html>'
        result = await renderer.render(html, images=images)
        assert result.pdf_binary is not None

    @pytest.mark.asyncio
    async def test_render_with_options(self, renderer):
        options = RenderOptions(
            page_size="letter",
            margin="1in",
            include_cover_page=True,
        )
        result = await renderer.render(
            "<html><body>Content</body></html>",
            options=options,
        )
        assert result.pdf_binary is not None

    def test_render_html_only(self, renderer):
        result = renderer.render_html_only("<html><body>Test</body></html>")
        assert result is not None
        assert "Test" in result

    def test_detect_mime_type_jpeg(self, renderer):
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        mime = renderer._detect_mime_type(jpeg_bytes)
        assert mime == "image/jpeg"

    def test_detect_mime_type_png(self, renderer):
        png_bytes = b"\x89PNG\r\n\x1a\n"
        mime = renderer._detect_mime_type(png_bytes)
        assert mime == "image/png"

    def test_detect_mime_type_unknown(self, renderer):
        unknown_bytes = b"\x00\x00\x00\x00"
        mime = renderer._detect_mime_type(unknown_bytes)
        assert mime == "image/jpeg"
