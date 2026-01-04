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
    async def complete_vision_structured(
        self,
        system: str,
        user: str,
        images: list[bytes],
        response_schema: dict[str, Any],
        schema_name: str = "response",
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

    @abstractmethod
    async def complete_structured(
        self,
        system: str,
        user: str,
        response_schema: dict[str, Any],
        schema_name: str = "response",
        model: str | None = None,
    ) -> str:
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

    def _prepare_schema_for_openai(self, schema: dict[str, Any]) -> dict[str, Any]:
        schema = schema.copy()
        if schema.get("type") == "object":
            schema["additionalProperties"] = False
            if "properties" in schema:
                schema["required"] = list(schema["properties"].keys())
                schema["properties"] = {
                    k: self._prepare_schema_for_openai(v)
                    for k, v in schema["properties"].items()
                }
        if "items" in schema:
            schema["items"] = self._prepare_schema_for_openai(schema["items"])
        if "$defs" in schema:
            schema["$defs"] = {
                k: self._prepare_schema_for_openai(v)
                for k, v in schema["$defs"].items()
            }
        for key in ("anyOf", "allOf", "oneOf"):
            if key in schema:
                schema[key] = [self._prepare_schema_for_openai(s) for s in schema[key]]
        return schema

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

    async def complete_structured(
        self,
        system: str,
        user: str,
        response_schema: dict[str, Any],
        schema_name: str = "response",
        model: str | None = None,
    ) -> str:
        """Complete with OpenAI's structured outputs (json_schema response_format)."""
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
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": self._prepare_schema_for_openai(response_schema),
                        },
                    },
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def complete_vision_structured(
        self,
        system: str,
        user: str,
        images: list[bytes],
        response_schema: dict[str, Any],
        schema_name: str = "response",
        model: str | None = None,
    ) -> str:
        """Vision completion with OpenAI's structured outputs."""
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

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
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
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": self._prepare_schema_for_openai(response_schema),
                        },
                    },
                },
            )
            if response.status_code != 200:
                import logging

                logging.error(
                    f"OpenAI vision structured request failed: {response.status_code}"
                )
                logging.error(f"Response body: {response.text[:1000]}")
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class AnthropicClient(LLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-sonnet-4-5",
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

        # Debug logging
        model_to_use = model or self.default_model
        url = f"{self.base_url}/messages"
        print(f"DEBUG: Anthropic API call - URL: {url}")
        print(f"DEBUG: Anthropic API call - Model: {model_to_use}")
        print(f"DEBUG: Anthropic API call - Tools count: {len(anthropic_tools)}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model_to_use,
                    "max_tokens": 4096,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                    "tools": anthropic_tools,
                },
            )
            print(f"DEBUG: Anthropic API response - Status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG: Anthropic API response - Body: {response.text}")
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

    async def complete_structured(
        self,
        system: str,
        user: str,
        response_schema: dict[str, Any],
        schema_name: str = "response",
        model: str | None = None,
    ) -> str:
        tool = {
            "name": schema_name,
            "description": "Respond with structured data matching this schema",
            "input_schema": response_schema,
        }

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
                    "tools": [tool],
                    "tool_choice": {"type": "tool", "name": schema_name},
                },
            )
            response.raise_for_status()
            result = response.json()

            for block in result.get("content", []):
                if block["type"] == "tool_use" and block["name"] == schema_name:
                    return json.dumps(block["input"])

            raise ValueError("No structured output returned from Anthropic")

    async def complete_vision_structured(
        self,
        system: str,
        user: str,
        images: list[bytes],
        response_schema: dict[str, Any],
        schema_name: str = "response",
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

        tool = {
            "name": schema_name,
            "description": "Respond with structured data matching this schema",
            "input_schema": response_schema,
        }

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
                    "tools": [tool],
                    "tool_choice": {"type": "tool", "name": schema_name},
                },
            )
            response.raise_for_status()
            result = response.json()

            for block in result.get("content", []):
                if block["type"] == "tool_use" and block["name"] == schema_name:
                    return json.dumps(block["input"])

            raise ValueError("No structured output returned from Anthropic")


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
