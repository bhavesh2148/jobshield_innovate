# ============================================================
# security/correlation_engine.py — Evidence & Risk Correlation Engine
# ============================================================
"""
JobShield Evidence & Risk Correlation Engine (Phase 4).

Unifies the two independent analytical paths:
- PATH 1 (Security Path): Observable artifacts & deterministic security rules
- PATH 2 (ML Path): Statistical ensemble (DistilBERT/XGBoost/LR) & FAISS vector memory

This engine:
1. Normalizes all signals into a disciplined, attributed evidence model (UnifiedFinding).
2. Synthesizes compound correlations across disparate signals.
3. Applies non-linear threat escalation policies (e.g., deterministic critical overrides).
4. Produces an authoritative unified risk posture, action, recommendation, and executive reasons.
"""

from typing import Optional
from dataclasses import dataclass
from api.schemas import (
    ArtifactReport,
    SecurityFinding,
    RuleSeverity,
    RiskLevel,
    RecommendationAction,
    EvidenceSource,
    FindingType,
    UnifiedFinding,
    FeatureReason
)


@dataclass
class CorrelationResult:
    risk_score: int
    risk_level: RiskLevel
    action: RecommendationAction
    recommendation: str
    unified_findings: list[UnifiedFinding]
    assessment_reasons: list[str]


def correlate_signals(
    artifacts: ArtifactReport,
    security_findings: list[SecurityFinding],
    ml_result: dict,
    similarity_info: dict,
    shap_reasons: list[FeatureReason],
    raw_content: str
) -> CorrelationResult:
    """
    Correlates security findings, ML probabilities, SHAP indicators,
    and vector memory into a unified evidence model and risk posture.
    """
    unified_findings: list[UnifiedFinding] = []
    assessment_reasons: list[str] = []

    final_prob = float(ml_result.get("final_prob", 0.0))
    ml_confidence = float(ml_result.get("confidence", 0.0))

    # ─────────────────────────────────────────────────────────────
    # 1. INGEST & ATTRIBUTE SECURITY RULE FINDINGS (Deterministic)
    # ─────────────────────────────────────────────────────────────
    has_critical_rule = False
    has_high_rule = False
    has_medium_rule = False

    for sf in security_findings:
        supporting = [sf.evidence_value] if sf.evidence_value else []
        unified_findings.append(
            UnifiedFinding(
                id=sf.id,
                source=EvidenceSource.RULE_ENGINE,
                finding_type=FindingType.DETERMINISTIC_RULE,
                severity=sf.severity,
                title=sf.title,
                description=sf.description,
                evidence_value=sf.evidence_value,
                supporting_artifacts=supporting,
                category=sf.category or "SECURITY_VIOLATION"
            )
        )
        if sf.severity == RuleSeverity.CRITICAL:
            has_critical_rule = True
        elif sf.severity == RuleSeverity.HIGH:
            has_high_rule = True
        elif sf.severity == RuleSeverity.MEDIUM:
            has_medium_rule = True

        assessment_reasons.append(f"[RULE ENGINE] {sf.title}: {sf.description}")

    # ─────────────────────────────────────────────────────────────
    # 2. INGEST & ATTRIBUTE ML MODEL INDICATORS (Statistical)
    # ─────────────────────────────────────────────────────────────
    if final_prob >= 0.70:
        ml_severity = RuleSeverity.HIGH
        ml_title = "High Statistical Similarity to Fraudulent Recruitment"
        ml_desc = (
            f"Contextual ML ensemble (DistilBERT + XGBoost + Logistic Regression) evaluates "
            f"an elevated statistical fraud likelihood ({round(final_prob * 100, 1)}%) based on "
            f"linguistic framing, compensation anomalies, and structural indicators."
        )
        unified_findings.append(
            UnifiedFinding(
                id="FINDING-ML-ELEVATED-FRAUD-PROB",
                source=EvidenceSource.ML_MODEL,
                finding_type=FindingType.MODEL_INDICATOR,
                severity=ml_severity,
                title=ml_title,
                description=ml_desc,
                evidence_value=f"{round(final_prob * 100, 1)}% fraud probability",
                supporting_artifacts=[f"Final Prob: {round(final_prob, 3)}", f"Confidence: {ml_confidence}%"],
                category="STATISTICAL_FRAUD_PATTERNS"
            )
        )
        assessment_reasons.append(f"[ML MODEL] {ml_title} ({round(final_prob * 100, 1)}% probability).")
    elif final_prob >= 0.40:
        ml_severity = RuleSeverity.MEDIUM
        ml_title = "Moderate Statistical Anomaly Signal"
        ml_desc = (
            f"ML models identify ambiguous or atypical recruitment phrasing ({round(final_prob * 100, 1)}% probability) "
            f"sharing stylistic characteristics with previously observed deceptive postings."
        )
        unified_findings.append(
            UnifiedFinding(
                id="FINDING-ML-MODERATE-FRAUD-PROB",
                source=EvidenceSource.ML_MODEL,
                finding_type=FindingType.MODEL_INDICATOR,
                severity=ml_severity,
                title=ml_title,
                description=ml_desc,
                evidence_value=f"{round(final_prob * 100, 1)}% fraud probability",
                supporting_artifacts=[f"Final Prob: {round(final_prob, 3)}"],
                category="STATISTICAL_FRAUD_PATTERNS"
            )
        )
        assessment_reasons.append(f"[ML MODEL] {ml_title} ({round(final_prob * 100, 1)}% probability).")

    # Attach top SHAP risk driver if significant
    risk_shap = []
    for r in shap_reasons:
        is_risk = r.get("is_risk", False) if isinstance(r, dict) else getattr(r, "is_risk", False)
        shap_val = float(r.get("shap_value", 0.0) if isinstance(r, dict) else getattr(r, "shap_value", 0.0))
        if is_risk and shap_val >= 0.05:
            risk_shap.append(r)

    if risk_shap:
        top_shap = risk_shap[0]
        feat = str(top_shap.get("feature", "feat") if isinstance(top_shap, dict) else getattr(top_shap, "feature", "feat"))
        label = str(top_shap.get("label", feat) if isinstance(top_shap, dict) else getattr(top_shap, "label", feat))
        val = top_shap.get("value", 0.0) if isinstance(top_shap, dict) else getattr(top_shap, "value", 0.0)
        s_val = float(top_shap.get("shap_value", 0.0) if isinstance(top_shap, dict) else getattr(top_shap, "shap_value", 0.0))
        msg = str(top_shap.get("message", "") if isinstance(top_shap, dict) else getattr(top_shap, "message", ""))
        unified_findings.append(
            UnifiedFinding(
                id=f"FINDING-SHAP-{feat.upper()}",
                source=EvidenceSource.ML_MODEL,
                finding_type=FindingType.MODEL_INDICATOR,
                severity=RuleSeverity.LOW,
                title=f"Structural Risk Factor: {label}",
                description=f"Model feature attribution indicates that '{label}' ({val}) elevated the fraud assessment.",
                evidence_value=f"SHAP: +{round(s_val, 3)}",
                supporting_artifacts=[msg] if msg else [],
                category="STATISTICAL_FEATURE_ATTRIBUTION"
            )
        )

    # ─────────────────────────────────────────────────────────────
    # 3. INGEST & ATTRIBUTE FAISS VECTOR MEMORY MATCH
    # ─────────────────────────────────────────────────────────────
    if similarity_info.get("boosted", False):
        sim_score = float(similarity_info.get("similarity_score", 0.0))
        top_snippet = str(similarity_info.get("top_match_snippet", ""))
        unified_findings.append(
            UnifiedFinding(
                id="FINDING-VECTOR-KNOWN-CAMPAIGN",
                source=EvidenceSource.VECTOR_MEMORY,
                finding_type=FindingType.SIMILARITY_MATCH,
                severity=RuleSeverity.MEDIUM,
                title="Semantic Similarity Match to Known Deceptive Campaign",
                description=(
                    f"Listing text exhibits close semantic alignment ({round(sim_score * 100, 1)}% similarity) "
                    f"with confirmed recruitment scam templates in JobShield's local vector memory."
                ),
                evidence_value=f"{round(sim_score * 100, 1)}% match",
                supporting_artifacts=[top_snippet[:120] if top_snippet else "Campaign template match"],
                category="KNOWN_CAMPAIGN_MATCH"
            )
        )
        assessment_reasons.append(
            f"[VECTOR MEMORY] Strong similarity match ({round(sim_score * 100, 1)}%) to historical fraudulent campaign."
        )

    # ─────────────────────────────────────────────────────────────
    # 4. COMPOUND CORRELATION SYNTHESIS (Cross-Signal Concurrence)
    # ─────────────────────────────────────────────────────────────
    rule_ids = {f.rule_id for f in security_findings}

    # Case A: Consumer Webmail + Off-Platform Communication
    if "RULE_CORPORATE_IDENTITY_MISMATCH" in rule_ids and "RULE_OFF_PLATFORM_COMMUNICATION" in rule_ids:
        unified_findings.append(
            UnifiedFinding(
                id="FINDING-COMPOUND-EVASIVE-COMMUNICATION",
                source=EvidenceSource.COMPOUND_CORRELATION,
                finding_type=FindingType.COMPOUND_SIGNAL,
                severity=RuleSeverity.HIGH,
                title="Compound Signal: Multi-Vector Evasive Communication",
                description=(
                    "The pairing of consumer webmail with unmonitored off-platform messaging (Telegram/WhatsApp) "
                    "strongly indicates deliberate evasion of corporate identity controls and platform monitoring."
                ),
                evidence_value="Webmail + Off-Platform Messaging",
                category="COMPOUND_EVASION"
            )
        )
        assessment_reasons.append(
            "[CORRELATION] Multi-vector evasion detected: Concurrent consumer webmail and off-platform screening."
        )

    # Case B: High Security Finding + Elevated ML Probability
    if has_high_rule and final_prob >= 0.60:
        unified_findings.append(
            UnifiedFinding(
                id="FINDING-COMPOUND-CORROBORATED-THREAT",
                source=EvidenceSource.COMPOUND_CORRELATION,
                finding_type=FindingType.COMPOUND_SIGNAL,
                severity=RuleSeverity.CRITICAL,
                title="Compound Signal: Rule Violation Corroborated by ML Pattern",
                description=(
                    "Deterministic security rule violations are independently corroborated by high statistical "
                    f"fraud probability ({round(final_prob * 100, 1)}%), confirming an active fraudulent operation."
                ),
                evidence_value=f"Deterministic Violation + {round(final_prob * 100, 1)}% ML Score",
                category="CORROBORATED_FRAUD"
            )
        )
        assessment_reasons.append(
            "[CORRELATION] Dual-path corroboration: Deterministic rule violation validated by statistical ML models."
        )

    # ─────────────────────────────────────────────────────────────
    # 5. UNIFIED RISK POSTURE SYNTHESIS
    # ─────────────────────────────────────────────────────────────
    ml_base_score = int(round(final_prob * 100))
    highest_severity = RuleSeverity.INFO

    for uf in unified_findings:
        if uf.severity == RuleSeverity.CRITICAL:
            highest_severity = RuleSeverity.CRITICAL
            break
        elif uf.severity == RuleSeverity.HIGH and highest_severity != RuleSeverity.CRITICAL:
            highest_severity = RuleSeverity.HIGH
        elif uf.severity == RuleSeverity.MEDIUM and highest_severity not in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]:
            highest_severity = RuleSeverity.MEDIUM

    # Non-linear escalation policy
    if highest_severity == RuleSeverity.CRITICAL:
        risk_score = max(85, ml_base_score)
        risk_level = RiskLevel.CRITICAL
        action = RecommendationAction.DO_NOT_ENGAGE
        recommendation = (
            "CRITICAL RISK: Active recruitment fraud pattern identified. Direct payment solicitation or critical "
            "identity impersonation detected. Cease all communication immediately. Never wire funds, transfer crypto, "
            "or provide personal identification."
        )
    elif highest_severity == RuleSeverity.HIGH:
        risk_score = max(65, ml_base_score)
        risk_level = RiskLevel.HIGH
        action = RecommendationAction.EXERCISE_CAUTION
        recommendation = (
            "HIGH RISK: Multiple deceptive recruitment indicators identified. High probability of social engineering. "
            "Do not disclose banking info or sensitive personal documents. Verify recruiter identity on the organization's "
            "official career portal."
        )
    elif highest_severity == RuleSeverity.MEDIUM or ml_base_score >= 35:
        risk_score = max(35, ml_base_score)
        risk_level = RiskLevel.MEDIUM
        action = RecommendationAction.VERIFY_OFFICIAL_CHANNELS
        recommendation = (
            "MEDIUM RISK: Unverified or irregular recruitment elements present. Contact the claimed organization's "
            "verified HR or talent acquisition department directly to validate the listing."
        )
    else:
        risk_score = min(30, ml_base_score)
        risk_level = RiskLevel.LOW
        action = RecommendationAction.PROCEED_NORMALLY
        recommendation = (
            "LOW RISK: No anomalous security patterns detected. The listing aligns with standard authentic recruitment "
            "practices. Normal professional due diligence recommended."
        )

    if not assessment_reasons:
        assessment_reasons.append("No anomalous security indicators or deceptive statistical patterns identified.")

    return CorrelationResult(
        risk_score=risk_score,
        risk_level=risk_level,
        action=action,
        recommendation=recommendation,
        unified_findings=unified_findings,
        assessment_reasons=assessment_reasons
    )
