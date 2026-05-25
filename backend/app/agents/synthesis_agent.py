import logging

from app.config import settings
from app.services.hosted_agents import invoke_hosted_agent
from app.services.llm_client import generate_agent_json
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

    if settings.LOCAL_LLM_MODE:
        try:
            return await generate_agent_json(
                agent_name="Synthesis Agent",
                system_prompt="Combine the supplied review outputs into the same JSON shape as the template. Return JSON only.",
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
            logger.warning("Local LLM synthesis failed; using fallback: %s", exc)
            return template

    if settings.DEMO_MODE:
        return template

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
