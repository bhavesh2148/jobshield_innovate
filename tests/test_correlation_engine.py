# ============================================================
# tests/test_correlation_engine.py — Phase 4 Correlation Tests
# ============================================================
import pytest
from security.artifact_extractor import extract_artifacts
from security.rule_engine import evaluate_security_rules
from security.correlation_engine import correlate_signals
from api.schemas import (
    RiskLevel,
    RecommendationAction,
    EvidenceSource,
    FindingType,
    RuleSeverity,
    SecurityFinding
)


def test_critical_rule_overrides_low_ml():
    """A direct payment/crypto solicitation must force CRITICAL risk even if ML probability is low."""
    text = "Join our elite team. Please transfer $150 via CashApp $OnboardingDep to secure your laptop."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules({}, artifacts, text)
    
    # Simulate a low ML score (e.g. well-phrased text that fooled the statistical model)
    ml_result = {
        "final_prob": 0.12,
        "confidence": 88.0,
        "prediction": "REAL"
    }
    similarity_info = {"boosted": False, "similarity_score": 0.1, "message": "", "top_match_snippet": ""}
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    assert res.risk_level == RiskLevel.CRITICAL
    assert res.action == RecommendationAction.DO_NOT_ENGAGE
    assert res.risk_score >= 85
    assert any(f.severity == RuleSeverity.CRITICAL and f.source == EvidenceSource.RULE_ENGINE for f in res.unified_findings)
    assert any("Direct Payment Solicitation" in r for r in res.assessment_reasons)


def test_high_ml_generates_model_indicator():
    """A high ML probability without rule violations must generate a MODEL_INDICATOR finding."""
    text = "Seeking remote assistants for general correspondence. Flexible hours and immediate start."
    artifacts = extract_artifacts(text)
    findings = []  # No deterministic rules triggered
    
    ml_result = {
        "final_prob": 0.85,
        "confidence": 85.0,
        "prediction": "FAKE"
    }
    similarity_info = {"boosted": False, "similarity_score": 0.2, "message": "", "top_match_snippet": ""}
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    assert res.risk_level == RiskLevel.HIGH
    assert res.risk_score >= 65
    ml_findings = [f for f in res.unified_findings if f.source == EvidenceSource.ML_MODEL]
    assert len(ml_findings) >= 1
    assert ml_findings[0].finding_type == FindingType.MODEL_INDICATOR
    assert "High Statistical Similarity" in ml_findings[0].title


def test_compound_correlation_webmail_and_offplatform():
    """Consumer mail paired with off-platform messaging must synthesize a compound evasion finding."""
    job_input = {"company": "Amazon"}
    text = "Amazon recruitment. Send resume to hr-jobs@gmail.com and connect on Telegram @AmazonLead for interview."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    
    ml_result = {
        "final_prob": 0.30,
        "confidence": 70.0,
        "prediction": "REAL"
    }
    similarity_info = {"boosted": False, "similarity_score": 0.1, "message": "", "top_match_snippet": ""}
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    compound_findings = [f for f in res.unified_findings if f.source == EvidenceSource.COMPOUND_CORRELATION]
    assert len(compound_findings) >= 1
    assert compound_findings[0].finding_type == FindingType.COMPOUND_SIGNAL
    assert "Evasive Communication" in compound_findings[0].title
    assert res.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


def test_dual_path_corroboration_escalates_to_critical():
    """When a HIGH deterministic rule is corroborated by elevated ML score, escalate to CRITICAL."""
    job_input = {"company": "Google"}
    text = "Urgent openings at Google. Contact recruiter-dept@gmail.com immediately."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    
    ml_result = {
        "final_prob": 0.72,
        "confidence": 72.0,
        "prediction": "FAKE"
    }
    similarity_info = {"boosted": False, "similarity_score": 0.3, "message": "", "top_match_snippet": ""}
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    assert res.risk_level == RiskLevel.CRITICAL
    assert res.action == RecommendationAction.DO_NOT_ENGAGE
    corroborated = [f for f in res.unified_findings if f.id == "FINDING-COMPOUND-CORROBORATED-THREAT"]
    assert len(corroborated) == 1


def test_benign_listing_clean_low_risk():
    """Authentic corporate listing with zero findings must return LOW risk and normal due diligence."""
    job_input = {"company": "Stripe"}
    text = "Stripe is looking for a backend engineer. Apply through our career page at https://stripe.com/jobs."
    artifacts = extract_artifacts(text)
    findings = evaluate_security_rules(job_input, artifacts, text)
    
    ml_result = {
        "final_prob": 0.05,
        "confidence": 95.0,
        "prediction": "REAL"
    }
    similarity_info = {"boosted": False, "similarity_score": 0.02, "message": "", "top_match_snippet": ""}
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    assert res.risk_level == RiskLevel.LOW
    assert res.action == RecommendationAction.PROCEED_NORMALLY
    assert res.risk_score <= 30
    assert len(res.unified_findings) == 0


def test_vector_memory_match_attribution():
    """Vector similarity match must be attributed to VECTOR_MEMORY with SIMILARITY_MATCH type."""
    text = "Standard data entry listing with template text."
    artifacts = extract_artifacts(text)
    findings = []
    
    ml_result = {
        "final_prob": 0.25,
        "confidence": 75.0,
        "prediction": "REAL"
    }
    similarity_info = {
        "boosted": True,
        "similarity_score": 0.89,
        "message": "Matched historical scam campaign template",
        "top_match_snippet": "Guaranteed $50/hr data entry remote job wire fee"
    }
    
    res = correlate_signals(artifacts, findings, ml_result, similarity_info, [], text)
    
    vector_findings = [f for f in res.unified_findings if f.source == EvidenceSource.VECTOR_MEMORY]
    assert len(vector_findings) == 1
    assert vector_findings[0].finding_type == FindingType.SIMILARITY_MATCH
    assert "Known Deceptive Campaign" in vector_findings[0].title
