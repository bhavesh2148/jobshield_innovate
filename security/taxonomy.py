# ============================================================
# security/taxonomy.py — Threat Taxonomy & MITRE ATT&CK Mapper
# ============================================================
"""
JobShield Phase 5: Threat Taxonomy & Structured Threat Classification.

Maps security findings, ML signals, and artifact patterns into formal
cybersecurity threat profiles with optional MITRE ATT&CK technique references.

Design principles:
- Profiles are generated from evidence, not assumed from surface heuristics.
- Each ThreatProfile has a confidence tier: CONFIRMED, PROBABLE, or SUSPECTED.
- MITRE ATT&CK tags are always sourced from real Enterprise/ICS technique IDs.
- This layer NEVER modifies risk scores. It only classifies and annotates.

MITRE ATT&CK references used:
  T1566     — Phishing (umbrella tactic: Initial Access)
  T1566.002 — Phishing: Spearphishing Link
  T1566.001 — Phishing: Spearphishing Attachment
  T1657     — Financial Theft (Impact)
  T1586     — Compromise Accounts (Resource Development)
  T1586.002 — Compromise Accounts: Email Accounts
  T1589     — Gather Victim Identity Information (Reconnaissance)
  T1589.001 — Gather Victim Identity Information: Credentials
  T1598     — Phishing for Information (Reconnaissance)
  T1598.003 — Phishing for Information: Spearphishing Link
  T1534     — Internal Spearphishing (Lateral Movement)
"""

from dataclasses import dataclass, field
from typing import Optional


# ── MITRE ATT&CK Technique Reference ─────────────────────────
@dataclass
class MitreTechniqueTag:
    technique_id: str          # e.g. "T1657"
    technique_name: str        # e.g. "Financial Theft"
    tactic: str                # e.g. "Impact"
    url: str                   # https://attack.mitre.org/techniques/T1657/
    relevance: str             # "HIGH" | "MEDIUM" | "LOW"


# ── Threat Profile ────────────────────────────────────────────
@dataclass
class ThreatProfile:
    attack_type: str           # e.g. "ADVANCE_FEE_FRAUD"
    profile_name: str          # Human-readable e.g. "Advance-Fee Recruitment Fraud"
    confidence: str            # "CONFIRMED" | "PROBABLE" | "SUSPECTED"
    description: str           # Analyst-facing explanation
    mitre_tags: list[MitreTechniqueTag] = field(default_factory=list)
    evidence_basis: list[str] = field(default_factory=list)  # Finding IDs


# ── Taxonomy Tag Library ──────────────────────────────────────
# Pre-defined MITRE ATT&CK tags relevant to recruitment fraud patterns.
_MITRE_T1566_002 = MitreTechniqueTag(
    technique_id="T1566.002",
    technique_name="Phishing: Spearphishing Link",
    tactic="Initial Access",
    url="https://attack.mitre.org/techniques/T1566/002/",
    relevance="HIGH",
)

_MITRE_T1657 = MitreTechniqueTag(
    technique_id="T1657",
    technique_name="Financial Theft",
    tactic="Impact",
    url="https://attack.mitre.org/techniques/T1657/",
    relevance="HIGH",
)

_MITRE_T1586_002 = MitreTechniqueTag(
    technique_id="T1586.002",
    technique_name="Compromise Accounts: Email Accounts",
    tactic="Resource Development",
    url="https://attack.mitre.org/techniques/T1586/002/",
    relevance="HIGH",
)

_MITRE_T1589_001 = MitreTechniqueTag(
    technique_id="T1589.001",
    technique_name="Gather Victim Identity Information: Credentials",
    tactic="Reconnaissance",
    url="https://attack.mitre.org/techniques/T1589/001/",
    relevance="HIGH",
)

_MITRE_T1598 = MitreTechniqueTag(
    technique_id="T1598",
    technique_name="Phishing for Information",
    tactic="Reconnaissance",
    url="https://attack.mitre.org/techniques/T1598/",
    relevance="MEDIUM",
)

_MITRE_T1534 = MitreTechniqueTag(
    technique_id="T1534",
    technique_name="Internal Spearphishing",
    tactic="Lateral Movement",
    url="https://attack.mitre.org/techniques/T1534/",
    relevance="LOW",
)

_MITRE_T1566_001 = MitreTechniqueTag(
    technique_id="T1566.001",
    technique_name="Phishing: Spearphishing Attachment",
    tactic="Initial Access",
    url="https://attack.mitre.org/techniques/T1566/001/",
    relevance="MEDIUM",
)


# ── Deterministic Profile Mapping ────────────────────────────
# Maps security finding categories to canonical threat profiles.
_CATEGORY_TO_PROFILE: dict[str, dict] = {
    "ADVANCE_FEE_FRAUD": {
        "attack_type": "ADVANCE_FEE_FRAUD",
        "profile_name": "Advance-Fee Recruitment Fraud",
        "description": (
            "Adversary solicits upfront financial transfer from job candidates under the pretense "
            "of onboarding fees, equipment purchases, or background check processing. Once payment "
            "is received, the adversary disappears with no employment materializing. Historically "
            "associated with the Nigerian 419-style fraud model adapted to employment platforms."
        ),
        "mitre_tags": [_MITRE_T1657, _MITRE_T1566_002],
    },
    "BRAND_IMPERSONATION": {
        "attack_type": "BRAND_IMPERSONATION",
        "profile_name": "Corporate Brand & Identity Impersonation",
        "description": (
            "Adversary exploits consumer trust in recognized enterprise brands (Google, Amazon, "
            "Stripe, etc.) by creating recruitment personas that falsely claim affiliation. "
            "Contact email domains are typically free consumer mail providers, inconsistent "
            "with the claimed organization's authentic corporate mail infrastructure. "
            "Classified as a social engineering / impersonation campaign."
        ),
        "mitre_tags": [_MITRE_T1586_002, _MITRE_T1566_002],
    },
    "CREDENTIAL_OR_PII_HARVESTING": {
        "attack_type": "CREDENTIAL_OR_PII_HARVESTING",
        "profile_name": "PII & Credential Harvesting Scheme",
        "description": (
            "Adversary uses recruitment pretexting to elicit sensitive personal information "
            "including Social Security numbers, government ID scans, financial account details, "
            "and corporate credentials. Generic form builder infrastructure (Google Forms, Typeform) "
            "is commonly deployed to harvest data outside of enterprise security monitoring perimeters."
        ),
        "mitre_tags": [_MITRE_T1589_001, _MITRE_T1598],
    },
    "OFF_PLATFORM_RECRUITMENT": {
        "attack_type": "OFF_PLATFORM_RECRUITMENT",
        "profile_name": "Off-Platform Screening Redirection",
        "description": (
            "Adversary redirects candidates off legitimate job boards and into unmonitored "
            "messaging channels (Telegram, WhatsApp) to bypass platform anti-fraud telemetry, "
            "audit logging, and automated account suspension. Private channel isolation is "
            "characteristic of social engineering precursor stages before financial demands."
        ),
        "mitre_tags": [_MITRE_T1566_002, _MITRE_T1598],
    },
}

# Minimum ML probability thresholds for inferring profiles without rule triggers
_ML_INFER_PROB_THRESHOLD = 0.72
_ML_SIMILARITY_THRESHOLD = 0.80


def classify_threat_profiles(
    security_findings: list,
    ml_result: dict,
    artifacts,
    similarity_info: dict,
) -> list[ThreatProfile]:
    """
    Classifies the threat evidence into structured ThreatProfile objects.

    Sources of evidence processed in priority order:
    1. Deterministic security rule findings (highest confidence)
    2. ML ensemble probability + FAISS similarity memory (probable/suspected)
    3. Artifact pattern analysis (PII harvesting forms) as fallback

    Returns a deduplicated list of ThreatProfiles ordered by confidence.
    """
    profiles: dict[str, ThreatProfile] = {}

    # ── 1. DETERMINISTIC RULE FINDINGS ───────────────────────
    for finding in security_findings:
        category = getattr(finding, "category", None) or finding.get("category") if isinstance(finding, dict) else finding.category
        finding_id = getattr(finding, "id", None) or (finding.get("id") if isinstance(finding, dict) else finding.id)

        if not category or category not in _CATEGORY_TO_PROFILE:
            continue

        template = _CATEGORY_TO_PROFILE[category]

        if category not in profiles:
            profiles[category] = ThreatProfile(
                attack_type=template["attack_type"],
                profile_name=template["profile_name"],
                confidence="CONFIRMED",
                description=template["description"],
                mitre_tags=template["mitre_tags"],
                evidence_basis=[finding_id] if finding_id else [],
            )
        else:
            if finding_id and finding_id not in profiles[category].evidence_basis:
                profiles[category].evidence_basis.append(finding_id)

    # ── 2. ML PROBABILITY + SIMILARITY MEMORY INFERENCE ──────
    final_prob = float(ml_result.get("final_prob", 0.0))
    similarity_score = float(similarity_info.get("similarity_score", 0.0))

    if final_prob >= _ML_INFER_PROB_THRESHOLD or similarity_score >= _ML_SIMILARITY_THRESHOLD:
        # If ML alone predicts high-probability fraud without rule confirmation,
        # tag with a generic phishing profile at PROBABLE confidence
        if "ADVANCE_FEE_FRAUD" not in profiles and "BRAND_IMPERSONATION" not in profiles:
            confidence = "CONFIRMED" if similarity_score >= _ML_SIMILARITY_THRESHOLD else "PROBABLE"

            profiles["ML_INFERRED_FRAUD"] = ThreatProfile(
                attack_type="ML_INFERRED_FRAUD",
                profile_name="ML-Detected Recruitment Fraud Pattern",
                confidence=confidence,
                description=(
                    "Statistical ML ensemble analysis detected significant linguistic and structural "
                    "anomalies consistent with fraudulent recruitment campaigns. The specific fraud "
                    "mechanism was not confirmed by deterministic artifact analysis, suggesting "
                    "sophisticated adversary tradecraft or lightly obfuscated presentation. "
                    "Probability-weighted ensemble score exceeds fraud detection threshold."
                ),
                mitre_tags=[_MITRE_T1566_002, _MITRE_T1598],
                evidence_basis=["ML_ENSEMBLE", "FAISS_SIMILARITY"] if similarity_score >= _ML_SIMILARITY_THRESHOLD else ["ML_ENSEMBLE"],
            )

    # ── 3. ARTIFACT-LEVEL PII HARVESTING DETECTION ───────────
    # If unmonitored form links were found in URLs but no rule fired (edge case)
    FORM_DOMAINS = {"docs.google.com", "forms.gle", "typeform.com", "jotform.com", "surveymonkey.com"}
    if artifacts and hasattr(artifacts, "urls"):
        for url_artifact in artifacts.urls:
            url_domain = (url_artifact.domain or "").lower()
            if any(fd in url_domain for fd in FORM_DOMAINS):
                if "CREDENTIAL_OR_PII_HARVESTING" not in profiles:
                    profiles["CREDENTIAL_OR_PII_HARVESTING"] = ThreatProfile(
                        attack_type="CREDENTIAL_OR_PII_HARVESTING",
                        profile_name="PII & Credential Harvesting Scheme",
                        confidence="SUSPECTED",
                        description=_CATEGORY_TO_PROFILE["CREDENTIAL_OR_PII_HARVESTING"]["description"],
                        mitre_tags=_CATEGORY_TO_PROFILE["CREDENTIAL_OR_PII_HARVESTING"]["mitre_tags"],
                        evidence_basis=[f"URL:{url_artifact.value[:50]}"],
                    )
                break

    # ── ORDER BY CONFIDENCE (CONFIRMED → PROBABLE → SUSPECTED) ─
    confidence_order = {"CONFIRMED": 0, "PROBABLE": 1, "SUSPECTED": 2}
    sorted_profiles = sorted(profiles.values(), key=lambda p: confidence_order.get(p.confidence, 3))

    return sorted_profiles
