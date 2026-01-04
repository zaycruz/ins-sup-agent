from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.vision import SYSTEM_PROMPT, format_user_prompt
from src.schemas.evidence import VisionEvidence


class VisionEvidenceAgent(BaseAgent[VisionEvidence]):
    name = "vision_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            photo_id=context["photo_id"],
            job_type=context.get("job_type", "storm_damage"),
            damage_type=context.get("damage_type", "hail_and_wind"),
            roof_type=context.get("roof_type", "asphalt_shingle"),
            roof_squares=context.get("roof_squares", 0.0),
            additional_notes=context.get("additional_notes"),
        )

    async def run(self, context: dict[str, Any]) -> VisionEvidence:
        self.logger.info(f"Processing photo: {context.get('photo_id')}")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)
            image_bytes = context.get("image_bytes")

            if image_bytes is None:
                raise ValueError("image_bytes is required in context")

            images = [image_bytes] if isinstance(image_bytes, bytes) else image_bytes

            schema = VisionEvidence.model_json_schema()
            response = await self.llm.complete_vision_structured(
                system=system_prompt,
                user=user_prompt,
                images=images,
                response_schema=schema,
                schema_name="vision_evidence",
                model=context.get("model"),
            )

            result = self._parse_response(response, VisionEvidence)

            self.logger.info(
                f"Detected {len(result.components)} components, "
                f"{len(result.global_observations)} observations"
            )
            return result

        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            raise

    async def run_batch(
        self,
        photos: list[dict[str, Any]],
        common_context: dict[str, Any] | None = None,
    ) -> list[VisionEvidence]:
        results: list[VisionEvidence] = []
        common_context = common_context or {}

        for photo in photos:
            context = {**common_context, **photo}
            try:
                result = await self.run(context)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Failed to process photo {photo.get('photo_id')}: {e}"
                )
                raise

        return results
