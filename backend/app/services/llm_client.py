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

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"Could not parse JSON object from LLM output: {text[:300]}")


def _error_result(agent_name: str, template: dict, exc: Exception) -> dict:
    """Return a schema-compatible object that makes local LLM failures obvious.

    Agent files may still contain legacy try/except fallback code. Returning an
    explicit object instead of raising prevents those wrappers from replacing the
    failure with normal-looking deterministic demo output.
    """
    message = f"{type(exc).__name__}: {exc}"
    result = dict(template)
    result["error"] = f"{agent_name} local LLM call failed: {message}"
    result["agent_name"] = agent_name
    result["tool_results"] = [
        {
            "tool_name": "local_llm_call",
            "status": "fail",
            "detail": result["error"],
        }
    ]
    result["checks_performed"] = [
        {
            "rule": "Local LLM invocation",
            "result": "fail",
            "detail": result["error"],
        }
    ]
    if "summary" in result:
        result["summary"] = result["error"]
    if "clinical_summary" in result:
        result["clinical_summary"] = result["error"]
    if "clinical_rationale" in result:
        result["clinical_rationale"] = result["error"]
    if "recommendation" in result:
        result["recommendation"] = "pend_for_review"
    if "confidence" in result:
        result["confidence"] = 0.0
    if "confidence_level" in result:
        result["confidence_level"] = "LOW"
    if "disclaimer" in result:
        result["disclaimer"] = "Local LLM call failed. Check backend logs, OPENAI_API_KEY, OPENAI_MODEL, quota and base URL configuration."
    return result


async def generate_agent_json(
    *,
    agent_name: str,
    system_prompt: str,
    payload: dict,
    template: dict,
) -> dict:
    """Call the configured LLM and return a JSON object."""
    if not settings.LLM_MODEL:
        return _error_result(agent_name, template, RuntimeError("LOCAL_LLM_MODE is enabled but LLM_MODEL/OPENAI_MODEL is not set"))

    client = _get_client()

    user_prompt = {
        "task": f"Return the {agent_name} result as a single JSON object only.",
        "strict_requirements": [
            "Return valid JSON only. No markdown. No commentary.",
            "Keep the same top-level keys and compatible value types as the template.",
            "Do not include PHI beyond what the user supplied.",
            "This is a research prototype. Do not present the output as a final clinical or payer determination.",
        ],
        "input_payload": payload,
        "json_template_shape": template,
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

    try:
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
        logger.info("%s produced local LLM JSON output", agent_name)
        return result
    except Exception as exc:
        logger.exception("%s local LLM call failed", agent_name)
        return _error_result(agent_name, template, exc)
