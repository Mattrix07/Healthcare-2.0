"""Clinical Reviewer Agent — local LLM, demo, or hosted dispatch."""

import logging

from app.config import settings
from app.services.hosted_agents import invoke_hosted_agent
from app.services.llm_client import generate_agent_json
from app.services.runtime import use_demo_mode, use_llm_mode
from app.agents.demo_outputs import build_demo_clinical_result

logger = logging.getLogger(__name__)


def _request_mode(request_data: dict) -> str | None:
    mode = request_data.get("runtime_mode")
    return str(mode).strip().lower() if mode else None


async def run_clinical_review(request_data: dict) -> dict:
    """Run Clinical Reviewer Agent using local LLM, demo stub, or hosted agent."""
    template = build_demo_clinical_result(request_data)
    mode = _request_mode(request_data)

    if mode == "demo" or (mode is None and use_demo_mode()):
        return template

    if mode == "llm" or (mode is None and use_llm_mode()):
        try:
            return await generate_agent_json(
                agent_name="Clinical Reviewer Agent",
                system_prompt=(
                    "You are a healthcare prior authorization clinical reviewer agent. "
                    "Extract clinical facts from the submitted notes, validate code format at a high level, "
                    "identify clinical rationale, prior treatments, severity, diagnostics, and gaps. "
                    "Do not invent external records or claim live database access. Do not make a final payer decision."
                ),
                payload=request_data,
                template=template,
            )
        except Exception as exc:
            if settings.LLM_FALLBACK_TO_DEMO:
                logger.warning("Local LLM clinical agent failed; using demo output: %s", exc)
                return template
            raise

    return await invoke_hosted_agent(
        "clinical-reviewer-agent",
        settings.HOSTED_AGENT_CLINICAL_URL,
        request_data,
        foundry_agent_name=settings.HOSTED_AGENT_CLINICAL_NAME,
    )
