# ============================================================
# explainability/explainer.py — SHAP + phrase highlighting
# ============================================================

import re
import numpy as np
import shap
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import SPAM_KEYWORDS, FREE_EMAIL_DOMAINS


# ── Human-readable feature labels ────────────────────────────
FEATURE_LABELS = {
    "has_salary":           "Salary range provided",
    "has_free_email":       "Uses non-official email domain (e.g. Gmail)",
    "has_company_profile":  "Company profile/description present",
    "has_logo":             "Company logo present",
    "has_questions":        "Application screening questions present",
    "telecommuting":        "Remote/telecommuting position",
    "has_experience_req":   "Experience requirement specified",
    "spam_keyword_count":   "High urgency/spam keyword frequency",
    "uppercase_ratio":      "Excessive use of ALL CAPS",
    "description_length":   "Job description length",
    "title_length":         "Job title length",
}

RISK_MESSAGES = {
    "has_free_email":       "Uses non-official email (Gmail/Yahoo)",
    "spam_keyword_count":   "Contains urgency or scam keywords",
    "uppercase_ratio":      "Excessive capitalization (spam indicator)",
    "has_salary":           "No salary information provided",
    "has_company_profile":  "Missing or very thin company profile",
    "has_logo":             "No company logo present",
    "has_questions":        "No application screening questions",
    "description_length":   "Unusually short job description",
}


class Explainer:
    """
    Wraps SHAP TreeExplainer for XGBoost and a custom
    attention-based highlighter for BERT outputs.
    Produces human-readable explanations.
    """

    def __init__(self, xgb_model, feature_names: list[str]):
        self.feature_names = feature_names
        logger.info("Building SHAP TreeExplainer...")
        self.shap_explainer = shap.TreeExplainer(xgb_model.model)

    def explain_structured(
        self,
        structured_features: np.ndarray,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Return top-K SHAP-based reasons for the prediction.

        Parameters
        ----------
        structured_features : np.ndarray
            Single sample, shape (n_features,).

        Returns
        -------
        list of dicts:  {feature, value, shap_value, direction, message}
        """
        X = structured_features.reshape(1, -1)
        shap_values = self.shap_explainer.shap_values(X)

        # For binary XGBoost, shap_values may be list[2] (one per class)
        if isinstance(shap_values, list):
            sv = shap_values[1][0]   # FAKE class
        else:
            sv = shap_values[0]

        # Pair feature names with their SHAP values
        pairs = list(zip(self.feature_names, sv, structured_features.flatten()))
        # Sort by absolute SHAP value descending
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)

        reasons = []
        for feat_name, sv_val, feat_val in pairs[:top_k]:
            direction = "increases" if sv_val > 0 else "decreases"
            label = FEATURE_LABELS.get(feat_name, feat_name.replace("_", " ").title())
            risk_msg = RISK_MESSAGES.get(feat_name, label)

            reasons.append({
                "feature": feat_name,
                "label": label,
                "value": round(float(feat_val), 3),
                "shap_value": round(float(sv_val), 4),
                "direction": direction,
                "message": risk_msg,
                "is_risk": sv_val > 0,
            })

        return reasons

    def format_human_explanation(self, reasons: list[dict], prediction: str) -> str:
        """
        Convert SHAP reasons to a plain-language explanation.

        Example output:
        "This job is likely FAKE because:
        - Uses non-official email domain (Gmail/Yahoo)
        - High urgency/spam keyword frequency
        ..."
        """
        verb = "likely FAKE" if prediction == "FAKE" else "likely REAL"
        risk_reasons = [r for r in reasons if r["is_risk"]][:3]
        safe_reasons = [r for r in reasons if not r["is_risk"]][:2]

        lines = [f"This job is {verb} because:"]

        if prediction == "FAKE":
            for r in risk_reasons:
                lines.append(f"  • {r['message']}")
            if safe_reasons:
                lines.append("\nFactors suggesting it might be real:")
                for r in safe_reasons:
                    lines.append(f"  • {r['message']}")
        else:
            for r in safe_reasons:
                lines.append(f"  • {r['message']}")
            if risk_reasons:
                lines.append("\nNote — some risk factors still present:")
                for r in risk_reasons[:2]:
                    lines.append(f"  • {r['message']}")

        return "\n".join(lines)


# ── Suspicious Phrase Highlighter ────────────────────────────
def highlight_suspicious_phrases(text: str) -> list[dict]:
    """
    Find positions of spam keywords and free email domains
    in the job text. Returns list of {phrase, start, end}.
    """
    highlights = []
    text_lower = text.lower()

    suspicious_terms = SPAM_KEYWORDS + list(FREE_EMAIL_DOMAINS)

    for term in suspicious_terms:
        for match in re.finditer(re.escape(term), text_lower):
            highlights.append({
                "phrase": match.group(),
                "start": match.start(),
                "end": match.end(),
            })

    # Deduplicate overlapping spans
    highlights.sort(key=lambda x: x["start"])
    merged = []
    for h in highlights:
        if merged and h["start"] < merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], h["end"])
            merged[-1]["phrase"] += f" / {h['phrase']}"
        else:
            merged.append(h)

    return merged
