import logging

from app.config import settings
from app.services.hosted_agents import invoke_hosted_agent
from app.services.llm_client import generate_agent_json
from app.services.runtime import use_demo_mode, use_llm_mode
from app.agents.demo_outputs import build_demo_synthesis_result

logger = logging.getLogger(__name__)


async def run_synthesis_review(
    request_data: dict,
    compliance_result: dict,
    clinical_result: dict,
    coverage_result: dict,
    cpt_validation: dict | None = None,
) -> dict:
    template = build_demo_synthesis_result(
        request_data=request_data,
        compliance_result=compliance_result,
        clinical_result=clinical_result,
        coverage_result=coverage_result,
        cpt_validation=cpt_validation,
    )

    if use_demo_mode():
        return template

    if use_llm_mode():
        try:
            return await generate_agent_json(
                agent_name="Synthesis Agent",
                system_prompt=(
                    "You are a prior authorization synthesis agent. Combine the supplied agent outputs into "
                    "a final AI-assisted draft outcome using the same JSON shape as the template. "
                    "Use only the supplied evidence and return JSON only."
                ),
                payload={
                    "request": request_data,
                    "compliance_result": compliance_result,
                    "clinical_result": clinical_result,
                    "coverage_result": coverage_result,
                    "cpt_validation": cpt_validation,
                },
                template=template,
            )
        except Exception as exc:
            if settings.LLM_FALLBACK_TO_DEMO:
                logger.warning("Local LLM synthesis failed; using fallback: %s", exc)
                return template
            raise

    return await invoke_hosted_agent(
        "synthesis-decision-agent",
        settings.HOSTED_AGENT_SYNTHESIS_URL,
        {
            "request": request_data,
            "compliance_result": compliance_result,
            "clinical_result": clinical_result,
            "coverage_result": coverage_result,
            "cpt_validation": cpt_validation,
        },
        foundry_agent_name=settings.HOSTED_AGENT_SYNTHESIS_NAME,
    )
