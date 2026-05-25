"""Coverage Assessment Agent — local LLM, demo, or hosted dispatch."""

import logging

from app.config import settings
from app.services.hosted_agents import invoke_hosted_agent
from app.services.llm_client import generate_agent_json
from app.agents.demo_outputs import build_demo_coverage_result

logger = logging.getLogger(__name__)


async def run_coverage_review(request_data: dict, clinical_findings: dict) -> dict:
    """Run Coverage Assessment Agent using local LLM, demo stub, or hosted agent."""
    template = build_demo_coverage_result(request_data, clinical_findings)

    if settings.LOCAL_LLM_MODE:
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
            logger.warning("Local LLM coverage agent failed; using demo output: %s", exc)
            return template

    if settings.DEMO_MODE:
        return template

    return await invoke_hosted_agent(
        "coverage-assessment-agent",
        settings.HOSTED_AGENT_COVERAGE_URL,
        {
            "request": request_data,
            "clinical_findings": clinical_findings,
        },
        foundry_agent_name=settings.HOSTED_AGENT_COVERAGE_NAME,
    )
