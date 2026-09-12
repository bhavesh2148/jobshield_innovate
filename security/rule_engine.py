# ============================================================
# security/rule_engine.py — Deterministic Security Rule Engine
# ============================================================
"""
JobShield Deterministic Security Rule Engine.

Evaluates observable digital artifacts and job content against contextual
cybersecurity rules. Unlike statistical machine learning, these rules represent
deterministic, propositional security logic:

Rules Implemented:
1. RULE_ADVANCE_FEE_PAYMENT:
   Detects cryptocurrency addresses, P2P payment handles (CashApp, PayPal),
   or advance fee demands in employment context.
2. RULE_CORPORATE_IDENTITY_MISMATCH:
   Detects when a claimed organization (e.g., enterprise brand or stated company)
   uses consumer webmail (@gmail.com, @yahoo.com) or mismatched contact domains.
3. RULE_OFF_PLATFORM_COMMUNICATION:
   Detects recruitment outreach shifting candidates to unmonitored messaging
   channels (Telegram, WhatsApp) for screening or interviews.
4. RULE_UNOFFICIAL_APPLICATION_FORM:
   Detects generic third-party hosted forms (Google Forms, Typeform) used
   for applicant data harvesting instead of authentic enterprise ATS portals.
5. RULE_SUSPICIOUS_URGENCY_PAYMENT:
   Detects high-pressure urgency cues combined with payment vectors.
"""

import re
from typing import Optional
from api.schemas import (
    ArtifactReport, ArtifactType, SecurityFinding, RuleSeverity
)
from security.artifact_extractor import CONSUMER_MAIL_DOMAINS


# Known enterprise brands frequently impersonated in recruitment fraud
ENTERPRISE_BRANDS = {
    "google", "amazon", "microsoft", "apple", "meta", "facebook",
    "netflix", "cisco", "oracle", "ibm", "salesforce", "adobe",
    "paypal", "stripe", "spotify", "uber", "airbnb", "tesla",
    "intel", "nvidia", "accenture", "deloitte", "kpmg", "ey", "pwc",
    "jpmorgan", "goldman sachs", "morgan stanley", "walmart"
}

# High-pressure urgency phrases often paired with scam coercion
RE_URGENCY = re.compile(
    r'\b(?:urgent|immediately|within\s+24\s+hours?|act\s+fast|limited\s+slots?|wire\s+now|pay\s+before|forfeit\s+offer)\b',
    re.IGNORECASE
)


def evaluate_security_rules(
    job_input: dict,
    artifacts: ArtifactReport,
    raw_content: str
) -> list[SecurityFinding]:
    """
    Evaluates contextual security rules against extracted artifacts and job details.
    
    Returns a list of structured SecurityFinding objects.
    Does NOT modify ML probabilities or compute final risk scores.
    """
    findings: list[SecurityFinding] = []

    stated_company = str(job_input.get("company", "") or "").strip()
    job_title = str(job_input.get("title", "") or "").strip()
    lower_text = raw_content.lower()

    # Determine company context: stated company, or detected brand in text
    detected_brand = None
    if stated_company:
        detected_brand = stated_company.lower()
    else:
        for brand in ENTERPRISE_BRANDS:
            if re.search(r'\b' + re.escape(brand) + r'\b', lower_text):
                detected_brand = brand
                break

    # ─────────────────────────────────────────────────────────────
    # RULE 1: ADVANCE-FEE / DIRECT PAYMENT VECTOR (Severity: CRITICAL)
    # ─────────────────────────────────────────────────────────────
    # Legitimate employers never charge candidates for onboarding, hardware, or screening
    if artifacts.payment_identifiers:
        for p in artifacts.payment_identifiers:
            channel_type = p.metadata.get("payment_type", "p2p_transfer")
            if channel_type in ["cryptocurrency", "p2p_transfer"]:
                findings.append(
                    SecurityFinding(
                        id=f"FINDING-PAYMENT-{p.value.replace('$', '').replace('0x', '')[:8].upper()}",
                        rule_id="RULE_ADVANCE_FEE_PAYMENT",
                        title="Direct Payment Solicitation in Recruitment Context",
                        severity=RuleSeverity.CRITICAL,
                        description=(
                            f"Direct payment identifier ({p.value}) detected. Legitimate employers never "
                            f"require candidates to transfer funds, purchase equipment, or pay onboarding "
                            f"fees via cryptocurrency or P2P transfer applications."
                        ),
                        evidence_value=p.value,
                        category="ADVANCE_FEE_FRAUD"
                    )
                )

    # ─────────────────────────────────────────────────────────────
    # RULE 2: CORPORATE IDENTITY & DOMAIN MISMATCH (Severity: HIGH)
    # ─────────────────────────────────────────────────────────────
    if detected_brand:
        # Check if email contact uses a public consumer webmail domain
        for email in artifacts.emails:
            domain = email.domain or ""
            if domain in CONSUMER_MAIL_DOMAINS:
                findings.append(
                    SecurityFinding(
                        id="FINDING-IDENTITY-CONSUMER-MAIL",
                        rule_id="RULE_CORPORATE_IDENTITY_MISMATCH",
                        title="Claimed Corporate Identity Using Consumer Webmail",
                        severity=RuleSeverity.HIGH,
                        description=(
                            f"Recruitment communication claims affiliation with '{detected_brand.title()}', "
                            f"but directs correspondence to a free public email address ({email.value}). "
                            f"Legitimate enterprise talent acquisition teams operate exclusively on verified corporate domains."
                        ),
                        evidence_value=email.value,
                        category="BRAND_IMPERSONATION"
                    )
                )
                break  # Record one finding for consumer mail mismatch

    # ─────────────────────────────────────────────────────────────
    # RULE 3: OFF-PLATFORM INTERVIEW REDIRECTION (Severity: MEDIUM / HIGH)
    # ─────────────────────────────────────────────────────────────
    messaging_channels_found = set()
    for p in artifacts.payment_identifiers:
        if p.metadata.get("payment_type") == "messaging_channel":
            messaging_channels_found.add((p.metadata.get("channel", "messaging"), p.value))

    # Also check URLs or content for direct messaging redirection
    for url in artifacts.urls:
        if url.domain and any(ch in url.domain for ch in ["t.me", "telegram.me", "wa.me", "whatsapp.com"]):
            ch_name = "telegram" if "t.me" in url.domain or "telegram" in url.domain else "whatsapp"
            messaging_channels_found.add((ch_name, url.value))

    # Check text regex for direct mentions (e.g. Telegram @TechRecruiterHQ)
    msg_regex = re.compile(r'\b(telegram|whatsapp|signal)\s*(?:@|:|app|channel|handle)?\s*([@\w\d_\-\.]+)?', re.IGNORECASE)
    for m in msg_regex.finditer(raw_content):
        ch_name = m.group(1).lower()
        val = m.group(0).strip()
        messaging_channels_found.add((ch_name, val))

    for channel, val in messaging_channels_found:
        severity = RuleSeverity.HIGH if (artifacts.payment_identifiers or any(f.severity == RuleSeverity.HIGH for f in findings)) else RuleSeverity.MEDIUM
        findings.append(
            SecurityFinding(
                id=f"FINDING-OFF-PLATFORM-{channel.upper()}",
                rule_id="RULE_OFF_PLATFORM_COMMUNICATION",
                title=f"Off-Platform Interview Redirection ({channel.title()})",
                severity=severity,
                description=(
                    f"Candidate is instructed to conduct recruitment screening or onboarding over "
                    f"{channel.title()} ('{val}'). Threat actors use unmonitored personal messaging "
                    f"apps to bypass corporate security logging and platform abuse controls."
                ),
                evidence_value=val,
                category="OFF_PLATFORM_RECRUITMENT"
            )
        )

    # ─────────────────────────────────────────────────────────────
    # RULE 4: THIRD-PARTY HOSTED FORM FOR APPLICATION (Severity: MEDIUM)
    # ─────────────────────────────────────────────────────────────
    for url in artifacts.urls:
        if url.metadata.get("form_service") == "hosted_form":
            findings.append(
                SecurityFinding(
                    id="FINDING-HOSTED-FORM-PHISHING",
                    rule_id="RULE_UNOFFICIAL_APPLICATION_FORM",
                    title="Generic Hosted Web Form Used for Applicant Ingestion",
                    severity=RuleSeverity.MEDIUM,
                    description=(
                        f"Job application directs to an unverified third-party hosted form ({url.domain}). "
                        f"Generic forms are frequently used by threat actors to harvest PII, identity documents, "
                        f"and contact information without deploying legitimate Applicant Tracking Systems (ATS)."
                    ),
                    evidence_value=url.value,
                    category="CREDENTIAL_OR_PII_HARVESTING"
                )
            )

    # ─────────────────────────────────────────────────────────────
    # RULE 5: SUSPICIOUS URGENCY COERCION (Severity: HIGH when combined)
    # ─────────────────────────────────────────────────────────────
    urgency_match = RE_URGENCY.search(raw_content)
    if urgency_match and (artifacts.payment_identifiers or any(f.severity in [RuleSeverity.HIGH, RuleSeverity.CRITICAL] for f in findings)):
        findings.append(
            SecurityFinding(
                id="FINDING-URGENCY-COERCION",
                rule_id="RULE_SUSPICIOUS_URGENCY_PAYMENT",
                title="Artificial Urgency & Deadline Coercion",
                severity=RuleSeverity.HIGH,
                description=(
                    f"Recruiter applies high-pressure urgency phrasing ('{urgency_match.group(0)}') "
                    f"in conjunction with unverified contact or payment mechanisms. Social engineering "
                    f"exploits urgency to induce compliance before candidates verify authenticity."
                ),
                evidence_value=urgency_match.group(0),
                category="ADVANCE_FEE_FRAUD"
            )
        )

    return findings
