from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.report import SYSTEM_PROMPT, format_user_prompt


@dataclass
class ReportOutput:
    html_content: str
    pdf_bytes: bytes | None = None


TOOL_RENDER_PDF = {
    "type": "function",
    "function": {
        "name": "render_pdf",
        "description": "Render HTML content to a PDF document",
        "parameters": {
            "type": "object",
            "properties": {
                "html_content": {
                    "type": "string",
                    "description": "The HTML content to render as PDF",
                },
                "options": {
                    "type": "object",
                    "description": "PDF rendering options",
                    "properties": {
                        "page_size": {
                            "type": "string",
                            "enum": ["letter", "a4"],
                            "default": "letter",
                        },
                        "margin": {
                            "type": "string",
                            "default": "0.5in",
                        },
                    },
                },
            },
            "required": ["html_content"],
        },
    },
}


class ReportGeneratorAgent(BaseAgent[ReportOutput]):
    name = "report_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)
        self.tools = [TOOL_RENDER_PDF]

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            supplement_strategy=context["supplement_strategy"],
            estimate_interpretation=context["estimate_interpretation"],
            vision_evidence=context["vision_evidence"],
            job_metadata=context["job_metadata"],
            photo_data=context.get("photo_data"),
        )

    async def run(self, context: dict[str, Any]) -> ReportOutput:
        self.logger.info("Generating supplement report")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)

            response = await self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                model=context.get("model", "default"),
            )

            html_content = self._extract_html_from_response(response)

            pdf_bytes = None
            if context.get("render_pdf", False):
                pdf_bytes = await self._render_pdf(html_content, context)

            self.logger.info(
                f"Report generated: {len(html_content)} chars HTML"
                + (f", {len(pdf_bytes)} bytes PDF" if pdf_bytes else "")
            )
            return ReportOutput(html_content=html_content, pdf_bytes=pdf_bytes)

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise

    def _extract_html_from_response(self, response: str) -> str:
        response = response.strip()
        if response.startswith("```html"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    async def _render_pdf(
        self,
        html_content: str,
        context: dict[str, Any],
    ) -> bytes | None:
        # Placeholder - would integrate with PDF rendering service (e.g., weasyprint, puppeteer)
        self.logger.info("PDF rendering not yet implemented")
        return None

    def _parse_response(self, response: str, output_type: type) -> ReportOutput:
        # Override since ReportOutput is a dataclass, not Pydantic
        return ReportOutput(html_content=response)
