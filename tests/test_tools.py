from __future__ import annotations

import pytest

from src.tools.code_lookup import CodeLookupTool, CodeRequirement
from src.tools.examples import ExampleStore, SupplementExample
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
        # FL has enhanced requirements
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


class TestExampleStore:
    @pytest.fixture
    def store(self) -> ExampleStore:
        return ExampleStore()

    @pytest.mark.asyncio
    async def test_retrieve_by_query(self, store):
        results = await store.retrieve("decking water damage", limit=3)
        assert len(results) <= 3
        assert all(isinstance(r, SupplementExample) for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_by_carrier(self, store):
        results = await store.retrieve("shingles", carrier="State Farm", limit=5)
        # Should prioritize State Farm examples
        assert any(r.carrier == "State Farm" for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_by_type(self, store):
        results = await store.retrieve(
            "missing item", supplement_type="missing_line_item", limit=5
        )
        assert len(results) > 0

    def test_get_by_id(self, store):
        example = store.get_by_id("EX-001")
        assert example is not None
        assert example.example_id == "EX-001"

    def test_get_by_id_not_found(self, store):
        example = store.get_by_id("EX-999")
        assert example is None

    def test_get_by_type(self, store):
        examples = store.get_by_type("missing_line_item")
        assert len(examples) > 0
        assert all(e.supplement_type == "missing_line_item" for e in examples)

    def test_get_by_carrier(self, store):
        examples = store.get_by_carrier("State Farm")
        assert len(examples) > 0
        assert all(e.carrier == "State Farm" for e in examples)

    def test_get_approved_examples(self, store):
        approved = store.get_approved_examples()
        assert len(approved) > 0
        assert all(e.outcome == "approved" for e in approved)

    def test_get_all_tags(self, store):
        tags = store.get_all_tags()
        assert "decking" in tags
        assert "code_requirement" in tags


class TestPDFRenderer:
    @pytest.fixture
    def renderer(self) -> PDFRenderer:
        return PDFRenderer()

    @pytest.mark.asyncio
    async def test_render_simple_html(self, renderer):
        html = "<html><body><h1>Test</h1><p>Hello World</p></body></html>"
        result = await renderer.render(html)
        assert result.pdf_binary is not None
        assert result.page_count >= 1

    @pytest.mark.asyncio
    async def test_render_with_images(self, renderer, sample_photo_bytes):
        html = """
        <html>
        <body>
            <h1>Report</h1>
            <img src="{{IMAGE_photo_001}}" alt="Photo 1">
        </body>
        </html>
        """
        images = [
            ImageEmbed(
                photo_id="photo_001",
                binary=sample_photo_bytes,
                caption="Test photo",
            )
        ]
        result = await renderer.render(html, images=images)
        assert result.pdf_binary is not None
        # Image placeholder should be replaced
        assert b"{{IMAGE_photo_001}}" not in result.pdf_binary

    @pytest.mark.asyncio
    async def test_render_with_options(self, renderer):
        html = "<html><body><h1>Test</h1></body></html>"
        options = RenderOptions(
            page_size="letter",
            margin="1in",
            include_cover_page=True,
        )
        result = await renderer.render(html, options=options)
        assert result.pdf_binary is not None

    def test_render_html_only(self, renderer):
        html = "<h1>Test</h1><p>Content</p>"
        result = renderer.render_html_only(html)
        assert "<style>" in result
        assert "@page" in result
        assert "<h1>Test</h1>" in result

    def test_detect_mime_type_jpeg(self, renderer, sample_photo_bytes):
        mime = renderer._detect_mime_type(sample_photo_bytes)
        assert mime == "image/jpeg"

    def test_detect_mime_type_png(self, renderer):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mime = renderer._detect_mime_type(png_header)
        assert mime == "image/png"

    def test_detect_mime_type_unknown(self, renderer):
        unknown = b"unknown data"
        mime = renderer._detect_mime_type(unknown)
        assert mime == "image/jpeg"  # Default fallback
