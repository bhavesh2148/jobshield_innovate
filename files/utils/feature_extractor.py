# ============================================================
# utils/feature_extractor.py — Runtime feature extraction
# Converts raw API input → structured feature vector
# ============================================================

import re
import json
import pickle
import numpy as np
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    SPAM_KEYWORDS, FREE_EMAIL_DOMAINS,
    PROCESSED_DATA_DIR, CATEGORICAL_COLUMNS,
)

# Load scaler and encoders (cached after first load)
_scaler = None
_label_encoders = None
_feature_names = None


def _load_artifacts():
    global _scaler, _label_encoders, _feature_names
    if _scaler is None:
        scaler_path = PROCESSED_DATA_DIR / "scaler.pkl"
        le_path = PROCESSED_DATA_DIR / "label_encoders.pkl"
        fn_path = PROCESSED_DATA_DIR / "feature_names.json"

        if scaler_path.exists():
            with open(scaler_path, "rb") as f:
                _scaler = pickle.load(f)
        if le_path.exists():
            with open(le_path, "rb") as f:
                _label_encoders = pickle.load(f)
        if fn_path.exists():
            with open(fn_path) as f:
                _feature_names = json.load(f)


def extract_features_from_input(job_input: dict) -> np.ndarray:
    """
    Convert raw API input dictionary to a scaled structured
    feature vector, ready for XGBoost / LR inference.

    Expected keys in job_input:
        title, company, description, requirements, benefits,
        company_profile, salary_range, employment_type,
        required_experience, required_education,
        industry, function, telecommuting,
        has_company_logo, has_questions
    """
    _load_artifacts()

    def safe_str(key, default=""):
        return str(job_input.get(key, default) or default)

    def safe_int(key, default=0):
        try:
            return int(job_input.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    description = safe_str("description")
    company_profile = safe_str("company_profile")
    title = safe_str("title")
    requirements = safe_str("requirements")
    full_text = f"{title} {description} {requirements}"

    # ── Raw features (must match training order exactly) ──────
    features = {}

    # Salary presence
    salary = safe_str("salary_range")
    features["has_salary"] = 0 if not salary.strip() else 1

    # Free email domain
    all_text = description + " " + company_profile
    features["has_free_email"] = int(
        any(domain in all_text.lower() for domain in FREE_EMAIL_DOMAINS)
    )

    # Company profile
    features["has_company_profile"] = 0 if len(company_profile.strip()) < 20 else 1

    # Logo & questions
    features["has_logo"] = safe_int("has_company_logo")
    features["has_questions"] = safe_int("has_questions")
    features["telecommuting"] = safe_int("telecommuting")

    # Experience requirement
    exp = safe_str("required_experience")
    features["has_experience_req"] = 0 if not exp.strip() or exp.lower() == "not applicable" else 1

    # Spam keywords
    text_lower = full_text.lower()
    features["spam_keyword_count"] = sum(1 for kw in SPAM_KEYWORDS if kw in text_lower)

    # Uppercase ratio
    letters = [c for c in description if c.isalpha()]
    features["uppercase_ratio"] = (
        sum(1 for c in letters if c.isupper()) / len(letters) if letters else 0.0
    )

    # Lengths
    features["description_length"] = len(description)
    features["title_length"] = len(title)

    # Categorical encoding
    for col in CATEGORICAL_COLUMNS:
        key = f"enc_{col}"
        raw_val = safe_str(col) or "unknown"
        if _label_encoders and col in _label_encoders:
            le = _label_encoders[col]
            try:
                encoded = le.transform([raw_val])[0]
            except ValueError:
                encoded = 0  # unseen category → 0
        else:
            encoded = 0
        features[key] = encoded

    # Build ordered array matching training feature order
    if _feature_names:
        arr = np.array([features.get(fn, 0) for fn in _feature_names], dtype=np.float64)
    else:
        arr = np.array(list(features.values()), dtype=np.float64)

    # Scale
    if _scaler:
        arr = _scaler.transform(arr.reshape(1, -1)).flatten()

    return arr


def build_combined_text(job_input: dict) -> str:
    """
    Build the combined text string for BERT inference.
    Mirrors the preprocessing pipeline.
    """
    from data.preprocessor import clean_text
    text_fields = ["title", "company_profile", "description", "requirements", "benefits"]
    parts = []
    for field in text_fields:
        val = str(job_input.get(field, "") or "")
        cleaned = clean_text(val)
        if cleaned:
            parts.append(cleaned)
    return " [SEP] ".join(parts)
