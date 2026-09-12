import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from security.artifact_extractor import extract_artifacts
from security.rule_engine import evaluate_security_rules
from api.schemas import RuleSeverity


def test_payment_solicitation_rule():
    text = "Please transfer $200 via CashApp $RecruiterTeam or send to 0x71C84943E5FB54782F406085F169c3815D6438a6."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules({}, artifacts, text)
    
    rule_ids = [f.rule_id for f in findings]
    assert "RULE_ADVANCE_FEE_PAYMENT" in rule_ids
    payment_findings = [f for f in findings if f.rule_id == "RULE_ADVANCE_FEE_PAYMENT"]
    assert any(f.severity == RuleSeverity.CRITICAL for f in payment_findings)


def test_corporate_identity_consumer_mail_mismatch():
    job_input = {"company": "Google", "title": "Software Engineer"}
    text = "Send your resume and CV directly to careers-lead@gmail.com for review."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    
    rule_ids = [f.rule_id for f in findings]
    assert "RULE_CORPORATE_IDENTITY_MISMATCH" in rule_ids
    mismatch = next(f for f in findings if f.rule_id == "RULE_CORPORATE_IDENTITY_MISMATCH")
    assert mismatch.severity == RuleSeverity.HIGH
    assert "Google" in mismatch.description


def test_off_platform_communication():
    text = "We conduct all screening over Telegram @TechRecruiterHQ. Reach out to schedule."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules({}, artifacts, text)
    
    rule_ids = [f.rule_id for f in findings]
    assert "RULE_OFF_PLATFORM_COMMUNICATION" in rule_ids
    off_platform = next(f for f in findings if f.rule_id == "RULE_OFF_PLATFORM_COMMUNICATION")
    assert "Telegram" in off_platform.title


def test_hosted_form_harvesting():
    text = "Fill out our preliminary application here: https://forms.gle/xyz987654321 for verification."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules({}, artifacts, text)
    
    rule_ids = [f.rule_id for f in findings]
    assert "RULE_UNOFFICIAL_APPLICATION_FORM" in rule_ids
    form_finding = next(f for f in findings if f.rule_id == "RULE_UNOFFICIAL_APPLICATION_FORM")
    assert form_finding.severity == RuleSeverity.MEDIUM


def test_legitimate_listing_no_false_findings():
    job_input = {"company": "Stripe", "title": "Infrastructure Engineer"}
    text = "Stripe is seeking engineers. Apply at https://stripe.com/jobs or contact recruiting@stripe.com."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    
    # Corporate email matches, no payments, no forms, no off-platform channels
    assert len(findings) == 0


def test_typosquatting_domain_rule():
    job_input = {"company": "Infosys", "title": "Developer"}
    text = "Infosys is hiring! Submit application directly at https://inf0sys-careers.site."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    rule_ids = [f.rule_id for f in findings]
    assert any("RULE_TYPOSQUATTING_DOMAIN" in rid or "RULE_BRAND_HIJACKING_DOMAIN" in rid for rid in rule_ids)
    typo_finding = next(f for f in findings if "TYPOSQUATTING" in f.rule_id or "BRAND_HIJACKING" in f.rule_id)
    assert typo_finding.severity in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]

