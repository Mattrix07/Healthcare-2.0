"""Deterministic local demo outputs for an Australian private health workflow.

These helpers let the prototype run visibly without Azure, live payer systems,
hospital systems or external credentials. They return schema-shaped data so the
existing frontend can show the multi-agent workflow, agent details, draft review
rationale and audit trail.
"""

from __future__ import annotations


def _codes(request_data: dict, key: str) -> list[str]:
    return [str(c).strip().upper() for c in request_data.get(key, []) if str(c).strip()]


def _procedure_summary(request_data: dict) -> str:
    procedures = _codes(request_data, "procedure_codes")
    if not procedures:
        return "requested service"
    return ", ".join(procedures)


def build_demo_compliance_result(request_data: dict) -> dict:
    """Return a realistic AU payer checklist for local demonstrations."""
    missing_items: list[str] = []
    additional_info_requests: list[str] = []

    if not request_data.get("insurance_id"):
        missing_items.append("Member / policy number")
        additional_info_requests.append("Confirm active membership, product tier and policy number.")

    notes = str(request_data.get("clinical_notes", "")).strip()
    notes_lower = notes.lower()
    if len(notes) < 80:
        missing_items.append("Detailed clinical and admission notes")
        additional_info_requests.append("Submit fuller clinical notes supporting the proposed admission or service.")

    plan_context_present = any(term in notes_lower for term in ["hospital", "cover", "waiting", "excess", "gap", "admission", "prosthesis"])
    if not plan_context_present:
        missing_items.append("Private health context")
        additional_info_requests.append("Confirm hospital cover, waiting periods, excess or co-payment, agreement hospital status and gap arrangement.")

    overall_status = "complete" if not missing_items else "incomplete"

    checklist = [
        {"item": "Member demographics present", "status": "complete", "detail": f"Member and DOB captured for {request_data.get('patient_name', 'the member')}."},
        {"item": "Provider identifier present", "status": "complete" if request_data.get("provider_npi") else "missing", "detail": f"Provider identifier: {request_data.get('provider_npi') or 'not supplied'}."},
        {"item": "Diagnosis codes supplied", "status": "complete" if _codes(request_data, "diagnosis_codes") else "missing", "detail": f"Diagnosis codes: {', '.join(_codes(request_data, 'diagnosis_codes')) or 'none'}."},
        {"item": "MBS / procedure item numbers supplied", "status": "complete" if _codes(request_data, "procedure_codes") else "missing", "detail": f"Requested item(s): {_procedure_summary(request_data)}."},
        {"item": "Clinical rationale documented", "status": "complete" if len(notes) >= 80 else "incomplete", "detail": "Clinical notes provide a reviewable rationale." if len(notes) >= 80 else "Clinical notes are brief and should be expanded."},
        {"item": "Conservative treatment history documented", "status": "complete" if any(term in notes_lower for term in ["physio", "therapy", "medication", "conservative", "injection", "failed"]) else "incomplete", "detail": "Prior non-operative management is referenced." if any(term in notes_lower for term in ["physio", "therapy", "medication", "conservative", "injection", "failed"]) else "Prior treatment history is not clearly documented."},
        {"item": "Supporting diagnostics referenced", "status": "complete" if any(term in notes_lower for term in ["mri", "ct", "x-ray", "xray", "scan", "imaging", "pathology"]) else "incomplete", "detail": "Supporting diagnostic evidence is referenced." if any(term in notes_lower for term in ["mri", "ct", "x-ray", "xray", "scan", "imaging", "pathology"]) else "No explicit diagnostic result is referenced."},
        {"item": "Hospital cover and waiting-period context identified", "status": "complete" if plan_context_present else "incomplete", "detail": "Notes reference Australian private health context." if plan_context_present else "Hospital cover, waiting periods and excess/co-payment context require confirmation."},
        {"item": "Prosthesis / device consideration flagged", "status": "complete" if any(term in notes_lower for term in ["prosthesis", "device", "implant", "joint", "arthroplasty"]) else "incomplete", "detail": "Potential prosthesis or implant pathway identified." if any(term in notes_lower for term in ["prosthesis", "device", "implant", "joint", "arthroplasty"]) else "No prosthesis or implant consideration identified from submitted notes."},
        {"item": "Service type classified", "status": "complete", "detail": "Request classified as elective private hospital pre-admission review."},
    ]

    return {
        "agent_name": "AU Compliance Agent",
        "checklist": checklist,
        "overall_status": overall_status,
        "missing_items": missing_items,
        "additional_info_requests": additional_info_requests,
        "checks_performed": [{"rule": item["item"], "result": "pass" if item["status"] == "complete" else "warning", "detail": item["detail"]} for item in checklist],
    }


def build_demo_clinical_result(request_data: dict) -> dict:
    """Return a realistic clinical review output for local AU demonstrations."""
    diagnosis_codes = _codes(request_data, "diagnosis_codes")
    procedure_codes = _codes(request_data, "procedure_codes")
    notes = str(request_data.get("clinical_notes", "")).strip()

    diagnosis_validation = [{"code": code, "valid": True, "description": "Diagnosis code format accepted for demo review", "billable": "." in code or len(code) >= 3, "hierarchy_note": "Demo validation only; confirm official descriptor in production."} for code in diagnosis_codes]
    procedure_validation = [{"code": code, "valid": True, "description": "MBS-style item or procedure code accepted by local preflight validation", "source": "orchestrator_preflight"} for code in procedure_codes]

    return {
        "agent_name": "Clinical Reviewer Agent",
        "diagnosis_validation": diagnosis_validation,
        "procedure_validation": procedure_validation,
        "clinical_extraction": {
            "chief_complaint": "Elective private hospital service requiring review",
            "history_of_present_illness": notes[:500] or "Clinical notes were not provided in the demo request.",
            "prior_treatments": ["Physiotherapy and medication history to be verified", "Response to injections, conservative therapy or specialist management to be confirmed"],
            "severity_indicators": ["Pain, functional impairment or progression documented in submitted notes", "Requested treatment is framed as clinically indicated by the treating specialist"],
            "functional_limitations": ["Mobility, work or daily activity limitation requires reviewer confirmation from source documentation"],
            "diagnostic_findings": ["Imaging or diagnostic evidence referenced or required for criteria assessment"],
            "duration_and_progression": "Duration and progression should be confirmed from treating-provider records.",
            "medical_history_and_comorbidities": "Demo mode does not access external hospital, GP or insurer records.",
            "extraction_confidence": 82,
        },
        "literature_support": [{"title": "Evidence review placeholder for requested Australian private hospital service", "pmid": "DEMO-PMID", "relevance": "Represents where clinical evidence would be surfaced in a production workflow."}],
        "clinical_trials": [],
        "clinical_summary": "Demo clinical review completed. The submitted notes contain a reviewable clinical rationale, but a human reviewer should confirm source records, treating-specialist documentation and payer policy before any position is finalised.",
        "tool_results": [
            {"tool_name": "diagnosis_validation_demo", "status": "pass", "detail": f"{len(diagnosis_codes)}/{len(diagnosis_codes)} diagnosis codes accepted in demo validation."},
            {"tool_name": "clinical_extraction_demo", "status": "pass", "detail": "Clinical facts extracted from submitted notes without live EHR, hospital or insurer-system access."},
        ],
        "checks_performed": [
            {"rule": "Diagnosis-code validation", "result": "pass", "detail": "Diagnosis codes were structurally valid for demo purposes."},
            {"rule": "Clinical-evidence extraction", "result": "pass", "detail": "Key review facts were extracted from the submitted notes."},
        ],
    }


def build_demo_coverage_result(request_data: dict, clinical_findings: dict) -> dict:
    """Return a realistic AU private health coverage review output."""
    procedure_codes = _codes(request_data, "procedure_codes")
    criteria_assessment = [
        {"criterion": "Active member eligibility and hospital cover", "status": "MET" if request_data.get("insurance_id") else "INSUFFICIENT", "confidence": 74 if request_data.get("insurance_id") else 45, "evidence": ["Member / policy number supplied" if request_data.get("insurance_id") else "Member / policy number missing"], "notes": "Production workflow would verify active cover, product tier and waiting periods against insurer systems.", "source": "demo_au_policy_check", "met": bool(request_data.get("insurance_id"))},
        {"criterion": "MBS item alignment and proposed admission setting", "status": "MET" if procedure_codes else "INSUFFICIENT", "confidence": 78 if procedure_codes else 40, "evidence": [f"Requested item number(s): {', '.join(procedure_codes) or 'not supplied'}"], "notes": "Demo assumes the requested item can be assessed against an Australian private hospital pathway.", "source": "demo_au_policy_check", "met": bool(procedure_codes)},
        {"criterion": "Contracted hospital, gap and excess/co-payment position", "status": "INSUFFICIENT", "confidence": 55, "evidence": ["Hospital and gap details are referenced conceptually but not verified live."], "notes": "Reviewer should confirm hospital agreement status, medical gap arrangement, excess, co-payment and out-of-pocket implications.", "source": "demo_au_policy_check", "met": False},
        {"criterion": "Clinical documentation supports medical necessity", "status": "INSUFFICIENT", "confidence": 62, "evidence": [clinical_findings.get("clinical_summary", "Clinical summary unavailable") if isinstance(clinical_findings, dict) else "Clinical findings unavailable"], "notes": "Reviewer should confirm prior treatment, diagnostic findings, severity and treating-specialist recommendation.", "source": "demo_au_policy_check", "met": False},
        {"criterion": "Prosthesis / implant pathway considered", "status": "INSUFFICIENT", "confidence": 52, "evidence": ["Joint replacement scenario may involve prosthesis or implant considerations."], "notes": "Production workflow should check device/prosthesis rules and hospital billing context.", "source": "demo_au_policy_check", "met": False},
    ]
    documentation_gaps = [
        {"what": "Hospital agreement and gap scheme confirmation", "critical": True, "request": "Confirm planned hospital, contracting status, gap arrangement, excess and co-payment settings."},
        {"what": "Waiting period and pre-existing condition status", "critical": True, "request": "Confirm member has served relevant waiting periods and whether a pre-existing condition review is required."},
        {"what": "Clinical medical-necessity evidence", "critical": True, "request": "Confirm failed conservative therapy, diagnostic evidence, functional limitation and specialist recommendation from source records."},
        {"what": "Prosthesis or implant pathway", "critical": False, "request": "Confirm whether a prosthesis, implant or device applies and whether hospital billing aligns with policy rules."},
    ]
    if not request_data.get("insurance_id"):
        documentation_gaps.append({"what": "Active member eligibility", "critical": True, "request": "Provide member or policy number and eligibility confirmation."})

    return {
        "agent_name": "AU Coverage Agent",
        "provider_verification": {"npi": str(request_data.get("provider_npi", "")), "name": "Demo Orthopaedic Provider / Private Hospital", "specialty": "Specialty pending provider-number and hospital-contract verification", "status": "VERIFIED" if request_data.get("provider_npi") else "not_found", "detail": "Demo mode does not call live provider, hospital contract or insurer eligibility systems."},
        "coverage_policies": [{"policy_id": "AU-DEMO-PHF-001", "title": "Representative Australian private hospital criteria", "type": "AU_PRIVATE_HEALTH_POLICY", "relevant": True}],
        "criteria_assessment": criteria_assessment,
        "coverage_criteria_met": [item["criterion"] for item in criteria_assessment if item["status"] == "MET"],
        "coverage_criteria_not_met": [item["criterion"] for item in criteria_assessment if item["status"] != "MET"],
        "policy_references": ["AU-DEMO-PHF-001: Representative Australian private hospital criteria", "MBS item alignment and clinical indication review required before final position", "Hospital contract, gap, excess and waiting-period checks must be performed in insurer systems"],
        "coverage_limitations": ["Demo mode uses representative Australian private health criteria only; production requires payer-specific policy, eligibility and hospital-contract lookup."],
        "documentation_gaps": documentation_gaps,
        "tool_results": [
            {"tool_name": "provider_identifier_demo", "status": "pass" if request_data.get("provider_npi") else "warning", "detail": "Provider identifier captured; live provider-number and hospital-contract verification skipped in demo mode."},
            {"tool_name": "member_eligibility_demo", "status": "pass" if request_data.get("insurance_id") else "warning", "detail": "Member/policy number captured; active cover, waiting periods and excess/co-payment not verified live."},
            {"tool_name": "au_private_health_policy_demo", "status": "warning", "detail": "Representative AU private health criteria applied; payer-specific policy and billing rules not queried."},
        ],
        "checks_performed": [{"rule": item["criterion"], "result": "pass" if item["status"] == "MET" else "warning", "detail": item["notes"]} for item in criteria_assessment],
    }


def build_demo_synthesis_result(request_data: dict, compliance_result: dict, clinical_result: dict, coverage_result: dict, cpt_validation: dict | None = None) -> dict:
    """Return a final decision synthesis for local AU demonstrations."""
    item_ok = bool((cpt_validation or {}).get("valid", True))
    provider_ok = bool(coverage_result.get("provider_verification", {}).get("npi"))
    criteria = coverage_result.get("criteria_assessment", [])
    unmet = [c.get("criterion", "Unnamed criterion") for c in criteria if c.get("status") != "MET"]
    gaps = coverage_result.get("documentation_gaps", [])
    approve = item_ok and provider_ok and not unmet and not gaps
    recommendation = "approve" if approve else "pend_for_review"
    confidence = 0.84 if approve else 0.66
    confidence_level = "HIGH" if approve else "MEDIUM"
    missing_documentation = [gap.get("what", "Additional documentation") for gap in gaps if isinstance(gap, dict)]

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "confidence_level": confidence_level,
        "summary": "Demo synthesis indicates the case is eligible to fund based on visible criteria." if approve else "Demo synthesis recommends pending the request for human review because eligibility, hospital, gap, prosthesis or medical-necessity criteria require confirmation.",
        "clinical_rationale": clinical_result.get("clinical_summary", "Clinical rationale generated from submitted notes in demo mode."),
        "decision_gate": "GATE 1 (Member/provider): PASS | GATE 2 (Items/admission): PASS | GATE 3 (Funding and medical necessity): PASS" if approve else "GATE 1 (Member/provider): PASS | GATE 2 (Items/admission): PASS | GATE 3 (Funding and medical necessity): PEND",
        "coverage_criteria_met": coverage_result.get("coverage_criteria_met", []),
        "coverage_criteria_not_met": coverage_result.get("coverage_criteria_not_met", unmet),
        "missing_documentation": missing_documentation,
        "documentation_gaps": gaps,
        "policy_references": coverage_result.get("policy_references", []),
        "criteria_summary": f"{len(coverage_result.get('coverage_criteria_met', []))} of {len(criteria)} criteria met; remaining AU funding checks require reviewer confirmation.",
        "synthesis_audit_trail": {"mode": "local_demo_au_private_health", "item_preflight_valid": item_ok, "provider_present": provider_ok, "unmet_or_insufficient_criteria": unmet, "documentation_gaps": missing_documentation},
        "disclaimer": "Local demo output only. A human reviewer must validate member eligibility, policy rules, hospital contracting, item alignment, gap/excess settings, source clinical documentation and any prosthesis or device pathway before a final position is issued.",
    }
