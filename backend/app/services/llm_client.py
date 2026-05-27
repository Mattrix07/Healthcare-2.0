"""OpenAI-compatible LLM client for local/research agent mode.

This module intentionally avoids any Azure Foundry dependency. It can call any
provider that exposes an OpenAI-compatible Chat Completions endpoint, including
OpenAI, OpenRouter, Groq, Together, Nebius, LM Studio, Ollama OpenAI bridge, etc.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Create a cached AsyncOpenAI client using generic env config."""
    global _client
    if _client is not None:
        return _client

    kwargs: dict[str, Any] = {"api_key": settings.LLM_API_KEY or "local-key"}
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL.rstrip("/")

    _client = AsyncOpenAI(**kwargs)
    return _client


def _extract_json_object(text: str) -> dict:
    """Parse a JSON object from plain text or fenced markdown output."""
    text = (text or "").strip()
    if not text:
        raise ValueError("LLM returned empty content")

    # Remove common fenced code-block wrappers.
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: locate the first object-shaped region.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"Could not parse JSON object from LLM output: {text[:300]}")


def _blank_schema_shape(value: Any) -> Any:
    """Return a type-preserving blank schema shape without demo content.

    Agent templates are built from deterministic demo outputs, so sending the
    raw template to the model encourages it to copy demo strings such as
    `*_demo`, `DEMO-LCD`, and `Local demo output only`. This helper keeps only
    the JSON structure and value types.
    """
    if isinstance(value, dict):
        return {k: _blank_schema_shape(v) for k, v in value.items()}
    if isinstance(value, list):
        if not value:
            return []
        return [_blank_schema_shape(value[0])]
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return 0
    if isinstance(value, float):
        return 0.0
    if value is None:
        return None
    return ""


def _merge_missing_keys(result: dict, template: dict) -> dict:
    """Fill missing top-level keys from a blank template for API stability."""
    merged = dict(result)
    blanks = _blank_schema_shape(template)
    for key, value in blanks.items():
        merged.setdefault(key, value)
    return merged


async def generate_agent_json(
    *,
    agent_name: str,
    system_prompt: str,
    payload: dict,
    template: dict,
) -> dict:
    """Call the configured LLM and return a JSON object.

    Args:
        agent_name: Human-readable agent name for logging.
        system_prompt: Agent instructions.
        payload: Request/context payload to analyse.
        template: Schema-shaped object used only to derive a blank JSON shape.
    """
    if not settings.LLM_MODEL:
        raise RuntimeError("LLM mode is enabled but LLM_MODEL is not set")

    client = _get_client()
    blank_shape = _blank_schema_shape(template)

    user_prompt = {
        "task": f"Return the {agent_name} result as a single JSON object only.",
        "strict_requirements": [
            "Return valid JSON only. No markdown. No commentary.",
            "Use the supplied case data. Do not copy placeholder wording.",
            "Keep the same top-level keys and compatible value types as the blank JSON shape.",
            "Do not output demo labels such as *_demo, DEMO-LCD, Demo synthesis, or Local demo output only.",
            "Do not include patient information beyond what the user supplied.",
            "This is a research prototype. Human review is required before operational use.",
        ],
        "input_payload": payload,
        "blank_json_shape": blank_shape,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_prompt, default=str)},
    ]

    request_kwargs = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
    }

    # Prefer JSON mode where supported, but retry without it for providers that
    # implement only a subset of the OpenAI API.
    try:
        response = await client.chat.completions.create(
            **request_kwargs,
            response_format={"type": "json_object"},
        )
    except Exception as first_exc:
        logger.info(
            "%s JSON-mode call failed; retrying without response_format: %s",
            agent_name,
            first_exc,
        )
        response = await client.chat.completions.create(**request_kwargs)

    content = response.choices[0].message.content or ""
    result = _extract_json_object(content)
    result = _merge_missing_keys(result, template)
    logger.info("%s produced local LLM JSON output", agent_name)
    return result