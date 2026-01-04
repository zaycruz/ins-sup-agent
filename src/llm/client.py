from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx


class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list[bytes],
        model: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> dict[str, Any]:
        pass


class OpenAIClient(LLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.default_model = default_model
        self.base_url = base_url

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        if image_bytes[:4] == b"\x89PNG":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif (
            image_bytes[:4] == b"RIFF"
            and len(image_bytes) > 12
            and image_bytes[8:12] == b"WEBP"
        ):
            return "image/webp"
        elif image_bytes[:4] == b"GIF8":
            return "image/gif"
        return "image/jpeg"

    async def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
    ) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list[bytes],
        model: str | None = None,
    ) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": user}]

        for img in images:
            b64 = base64.b64encode(img).decode("utf-8")
            mime = self._detect_mime_type(img)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64}",
                        "detail": "high",
                    },
                }
            )

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4096,
                },
            )
            if response.status_code != 200:
                import logging

                logging.error(
                    f"OpenAI vision request failed: {response.status_code} to {url}"
                )
                logging.error(f"Response body: {response.text[:1000]}")
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]

            tool_calls = []
            for tc in result.get("tool_calls", []):
                tool_calls.append(
                    {
                        "id": tc["id"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                )

            return {
                "content": result.get("content", ""),
                "tool_calls": tool_calls,
            }


class AnthropicClient(LLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-sonnet-4-20250514",
        base_url: str = "https://api.anthropic.com/v1",
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.default_model = default_model
        self.base_url = base_url

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        if image_bytes[:4] == b"\x89PNG":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif (
            image_bytes[:4] == b"RIFF"
            and len(image_bytes) > 12
            and image_bytes[8:12] == b"WEBP"
        ):
            return "image/webp"
        elif image_bytes[:4] == b"GIF8":
            return "image/gif"
        return "image/jpeg"

    async def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
    ) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "max_tokens": 4096,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list[bytes],
        model: str | None = None,
    ) -> str:
        content: list[dict[str, Any]] = []

        for img in images:
            b64 = base64.b64encode(img).decode("utf-8")
            mime = self._detect_mime_type(img)
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": b64,
                    },
                }
            )

        content.append({"type": "text", "text": user})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "max_tokens": 4096,
                    "system": system,
                    "messages": [{"role": "user", "content": content}],
                },
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]

    async def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> dict[str, Any]:
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append(
                    {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get(
                            "parameters", {"type": "object", "properties": {}}
                        ),
                    }
                )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "max_tokens": 4096,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                    "tools": anthropic_tools,
                },
            )
            response.raise_for_status()
            result = response.json()

            tool_calls = []
            content = ""

            for block in result.get("content", []):
                if block["type"] == "text":
                    content = block["text"]
                elif block["type"] == "tool_use":
                    tool_calls.append(
                        {
                            "id": block["id"],
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block["input"]),
                            },
                        }
                    )

            return {"content": content, "tool_calls": tool_calls}


def get_vision_client() -> LLMClient:
    from src.config import settings

    provider = settings.vision_provider

    if provider.lower() == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            default_model=settings.vision_model,
            base_url=settings.openai_base_url,
        )
    elif provider.lower() == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            default_model=settings.vision_model,
            base_url=settings.anthropic_base_url,
        )
    else:
        raise ValueError(f"Unknown vision provider: {provider}")


def get_text_client() -> LLMClient:
    from src.config import settings

    provider = settings.text_provider

    if provider.lower() == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            default_model=settings.text_model,
            base_url=settings.anthropic_base_url,
        )
    elif provider.lower() == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            default_model=settings.text_model,
            base_url=settings.openai_base_url,
        )
    else:
        raise ValueError(f"Unknown text provider: {provider}")


def get_review_client() -> LLMClient:
    from src.config import settings

    provider = settings.text_provider

    if provider.lower() == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            default_model=settings.review_model,
            base_url=settings.anthropic_base_url,
        )
    elif provider.lower() == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            default_model=settings.review_model,
            base_url=settings.openai_base_url,
        )
    else:
        raise ValueError(f"Unknown review provider: {provider}")
