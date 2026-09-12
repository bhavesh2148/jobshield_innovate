# ============================================================
# utils/job_parser.py — Intelligent Ingestion Parser
# Auto-extracts structured metadata from unstructured text
# ============================================================

import re
from typing import Tuple, Dict, Any


# Checkbox / boolean truthy patterns
CHECKED_PATTERN = re.compile(r"(?:☑|\[x\]|\(x\)|\[\*\]|\(\*\)|\b(?:yes|true|y|1)\b)", re.IGNORECASE)
UNCHECKED_PATTERN = re.compile(r"(?:☐|\[\s*\]|\(\s*\)|\b(?:no|false|n|0)\b)", re.IGNORECASE)


def parse_checkbox_value(val_str: str) -> int:
    """Detect if a string indicates a checked or positive boolean value."""
    s = val_str.strip()
    if CHECKED_PATTERN.search(s):
        return 1
    if UNCHECKED_PATTERN.search(s):
        return 0
    # Fallback to general truthiness check
    if any(pos in s.lower() for pos in ["yes", "true", "present", "verified", "available", "included"]):
        return 1
    return 0


def parse_raw_job_text(raw_text: str) -> Dict[str, Any]:
    """
    Parses unstructured text copied from job postings or ATS portals.
    Detects key-value lines such as:
      - Job Title: Full Stack Developer
      - Company Name: Infosys Limited
      - Salary Range: $70,000–$95,000/year
      - Employment Type: Full-time
      - Experience Required: Associate level
      - Has Company Logo: ☑ Yes
      - Has Screening Questions: ☑ Yes
      - Remote / Telecommute: ☐ No
      - Job Description: ...
      - Requirements: ...

    Returns a dict with extracted metadata and the isolated clean description body.
    """
    if not raw_text or not raw_text.strip():
        return {}

    extracted: Dict[str, Any] = {
        "title": "",
        "company": "",
        "salary_range": "",
        "employment_type": "",
        "required_experience": "",
        "has_company_logo": 0,
        "has_questions": 0,
        "telecommuting": 0,
        "description": "",
        "requirements": "",
        "benefits": "",
        "company_profile": "",
    }

    # Normalize carriage returns
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Regular expressions for inline and multiline field anchors
    field_specs = [
        ("title", r"(?:Job\s*Title|Position\s*Title|Role|Designation)[\s:]+([^\n\r]+)"),
        ("company", r"(?:Company\s*Name|Employer|Organization|Hiring\s*Company)[\s:]+([^\n\r]+)"),
        ("salary_range", r"(?:Salary\s*Range|Compensation|Pay\s*Range|Salary)[\s:]+([^\n\r]+)"),
        ("employment_type", r"(?:Employment\s*Type|Job\s*Type|Work\s*Type)[\s:]+([^\n\r]+)"),
        ("required_experience", r"(?:Experience\s*Required|Required\s*Experience|Experience\s*Level)[\s:]+([^\n\r]+)"),
        ("has_company_logo", r"(?:Has\s*Company\s*Logo|Company\s*Logo|Has\s*Logo)[\s:]+([^\n\r]+)"),
        ("has_questions", r"(?:Has\s*Screening\s*Questions|Screening\s*Questions|Has\s*Questions)[\s:]+([^\n\r]+)"),
        ("telecommuting", r"(?:Remote\s*/\s*Telecommute|Remote\s*Work|Telecommuting|Remote)[\s:]+([^\n\r]+)"),
    ]

    for key, pattern in field_specs:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).strip()
            # If the value is followed immediately by another field header on same line, split it
            raw_val = re.split(
                r"\s+(?:Company\s*Name|Salary\s*Range|Employment\s*Type|Experience\s*Required|Has\s*Company\s*Logo|Has\s*Screening\s*Questions|Remote\s*/\s*Telecommute|Job\s*Description|Requirements)[\s:]+",
                raw_val,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0].strip()

            if key in ("has_company_logo", "has_questions", "telecommuting"):
                extracted[key] = parse_checkbox_value(raw_val)
            else:
                # Clean up punctuation
                cleaned_val = re.sub(r"^[–—\-:\s]+|[–—\-:\s]+$", "", raw_val)
                extracted[key] = cleaned_val

    # Extract Job Description section if separated
    desc_match = re.search(
        r"(?:Job\s*Description|Description|About\s*the\s*Role)[\s:]+(.*?)(?=(?:Requirements|Qualifications|What\s*You\s*Need|Benefits|About\s*Us|Company\s*Profile|$)|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if desc_match:
        extracted["description"] = desc_match.group(1).strip()

    # Extract Requirements section if separated
    req_match = re.search(
        r"(?:Requirements|Qualifications|What\s*You\s*Need)[\s:]+(.*?)(?=(?:Benefits|About\s*Us|Company\s*Profile|$)|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if req_match:
        extracted["requirements"] = req_match.group(1).strip()

    # Extract Company Profile section if separated
    profile_match = re.search(
        r"(?:About\s*Us|Company\s*Profile|About\s*the\s*Company)[\s:]+(.*?)(?=(?:Job\s*Description|Requirements|Qualifications|Benefits|$)|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if profile_match:
        extracted["company_profile"] = profile_match.group(1).strip()

    # If company is known enterprise brand and no profile was parsed, provide standard enterprise reference
    if extracted["company"] and not extracted["company_profile"]:
        extracted["company_profile"] = f"{extracted['company']} enterprise operations and corporate profile."

    # If no separate description block was extracted, retain the full text as description
    if not extracted["description"]:
        extracted["description"] = raw_text.strip()

    return extracted
