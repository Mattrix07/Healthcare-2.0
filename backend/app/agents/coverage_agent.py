"""Coverage Assessment Agent — local LLM, demo, or hosted dispatch."""

import logging

from app.config import settings
from app.services.hosted_agents import invoke_hosted_agent
from app.services.llm_client import generate_agent_json
from app.services.runtime import use_demo_mode, use_llm_mode
from app.agents.demo_outputs import build_demo_coverage_result

logger = logging.getLogger(__name__)


def _request_mode(request_data: dict) -> str | None:
    mode = request_data.get("runtime_mode")
    return str(mode).strip().lower() if mode else None


async def run_coverage_review(request_data: dict, clinical_findings: dict) -> dict:
    """Run Coverage Assessment Agent using local LLM, demo stub, or hosted agent."""
    template = build_demo_coverage_result(request_data, clinical_findings)
    mode = _request_mode(request_data)

    if mode == "demo" or (mode is None and use_demo_mode()):
        return template

    if mode == "llm" or (mode is None and use_llm_mode()):
        try:
            return await generate_agent_json(
                agent_name="Coverage Assessment Agent",
                system_prompt=(
                    "You are a prior authorization coverage assessment agent. "
                    "Review the request and clinical findings for provider details, representative criteria, "
                    "documentation gaps, and items that need human review. "
                    "Use only the payload provided. Return structured JSON only."
                ),
                payload={"request": request_data, "clinical_findings": clinical_findings},
                template=template,
            )
        except Exception as exc:
            if settings.LLM_FALLBACK_TO_DEMO:
                logger.warning("Local LLM coverage agent failed; using demo output: %s", exc)
                return template
            raise

    return await invoke_hosted_agent(
        "coverage-assessment-agent",
        settings.HOSTED_AGENT_COVERAGE_URL,
        {
            "request": request_data,
            "clinical_findings": clinical_findings,
        },
        foundry_agent_name=settings.HOSTED_AGENT_COVERAGE_NAME,
    )
