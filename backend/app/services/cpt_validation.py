"""MBS/procedure item format validation and curated lookup table.

Pre-agent validation layer:
  - Format validation: Australian MBS-style numeric items plus legacy CPT/HCPCS-compatible formats for demo compatibility
  - Lookup table: informational examples for common private hospital funding scenarios

This does NOT replace payer-specific code checks. It catches obvious typos and
provides descriptions for common items before agents run.
"""

import re


# --- Format validation ---

# AU MBS item numbers are commonly numeric. Allow 4-6 digits to keep the demo
# flexible for item numbers and hospital/procedure item variants.
_MBS_ITEM_PATTERN = re.compile(r"^\d{4,6}$")
# Keep CPT Category III and HCPCS-compatible patterns for backwards compatibility.
_CPT_CATEGORY_III_PATTERN = re.compile(r"^\d{4}T$")
_HCPCS_PATTERN = re.compile(r"^[A-V]\d{4,6}$")


def validate_code_format(code: str) -> dict:
    """Validate MBS/procedure item format.

    Returns dict with:
      code: the original code
      valid_format: True if format matches an accepted pattern
      code_type: "MBS item" | "CPT Category III" | "HCPCS-compatible" | "unknown"
      detail: human-readable message
    """
    code = code.strip().upper()

    if _MBS_ITEM_PATTERN.match(code):
        return {
            "code": code,
            "valid_format": True,
            "code_type": "MBS item",
            "detail": f"{code} — valid MBS-style numeric item format",
        }
    elif _CPT_CATEGORY_III_PATTERN.match(code):
        return {
            "code": code,
            "valid_format": True,
            "code_type": "CPT Category III",
            "detail": f"{code} — valid legacy CPT Category III-compatible format",
        }
    elif _HCPCS_PATTERN.match(code):
        return {
            "code": code,
            "valid_format": True,
            "code_type": "HCPCS-compatible",
            "detail": f"{code} — valid legacy HCPCS-compatible format",
        }
    else:
        return {
            "code": code,
            "valid_format": False,
            "code_type": "unknown",
            "detail": (
                f"{code} — invalid format. "
                "Expected a 4-6 digit MBS-style item number, CPT Category III-compatible code, or letter+digits code."
            ),
        }


# --- Curated lookup table for demo scenarios ---

_KNOWN_CODES: dict[str, dict] = {
    # Orthopaedic / private hospital examples
    "49518": {"description": "Total knee replacement / arthroplasty item example", "category": "Orthopaedics"},
    "48915": {"description": "Knee procedure associated item example", "category": "Orthopaedics"},
    "49318": {"description": "Hip replacement / arthroplasty item example", "category": "Orthopaedics"},
    "49118": {"description": "Arthroscopy / knee procedure item example", "category": "Orthopaedics"},
    # Cardiac / procedural examples
    "38200": {"description": "Coronary angiography item example", "category": "Cardiology"},
    "38306": {"description": "Cardiac catheterisation item example", "category": "Cardiology"},
    # Imaging / diagnostics
    "63560": {"description": "MRI knee item example", "category": "Imaging"},
    "56001": {"description": "CT imaging item example", "category": "Imaging"},
    # Oncology / infusion compatibility examples
    "96413": {"description": "Legacy infusion code retained for compatibility", "category": "Oncology"},
    "J9271": {"description": "Legacy drug code retained for compatibility", "category": "Oncology - Drug"},
}


def lookup_code(code: str) -> dict:
    """Look up a code in the curated demo table."""
    code = code.strip().upper()
    entry = _KNOWN_CODES.get(code)
    if entry:
        return {
            "code": code,
            "found": True,
            "description": entry["description"],
            "category": entry["category"],
        }
    return {
        "code": code,
        "found": False,
        "description": "",
        "category": "",
    }


def validate_procedure_codes(codes: list[str]) -> dict:
    """Validate a list of MBS/procedure item numbers: format check + curated lookup."""
    results = []
    all_valid = True

    for code in codes:
        fmt = validate_code_format(code)
        info = lookup_code(code)

        entry = {
            "code": fmt["code"],
            "valid_format": fmt["valid_format"],
            "code_type": fmt["code_type"],
            "known": info["found"],
            "description": info["description"],
            "category": info["category"],
            "detail": fmt["detail"],
        }

        if not fmt["valid_format"]:
            all_valid = False

        results.append(entry)

    total = len(results)
    valid_count = sum(1 for r in results if r["valid_format"])
    known_count = sum(1 for r in results if r["known"])

    summary = f"{valid_count}/{total} MBS/procedure items valid format"
    if known_count:
        summary += f", {known_count} recognized in demo lookup table"
    if not all_valid:
        invalid = [r["code"] for r in results if not r["valid_format"]]
        summary += f". INVALID: {', '.join(invalid)}"

    return {
        "valid": all_valid,
        "results": results,
        "summary": summary,
    }
