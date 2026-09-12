# ============================================================
# data/preprocessor.py — Full data pipeline with SMOTENC
# ============================================================

import re
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTENC

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATASET_FILENAME,
    TARGET_COLUMN, TEXT_COLUMNS, CATEGORICAL_COLUMNS,
    SPAM_KEYWORDS, FREE_EMAIL_DOMAINS, SMOTENC_RANDOM_STATE,
    SMOTENC_K_NEIGHBORS,
)


# ── Text Cleaning ────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Lowercase, strip HTML tags, remove special characters."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML
    text = re.sub(r"http\S+|www\S+", " ", text)   # strip URLs
    text = re.sub(r"[^a-zA-Z0-9\s.,!?'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def combine_text_fields(row: pd.Series) -> str:
    """Merge all text columns into one string."""
    parts = []
    for col in TEXT_COLUMNS:
        val = row.get(col, "")
        cleaned = clean_text(str(val))
        if cleaned:
            parts.append(cleaned)
    return " [SEP] ".join(parts)


# ── Structured Feature Engineering ──────────────────────────
def extract_email_domain(email: str) -> str:
    """Return domain from email string."""
    if not isinstance(email, str):
        return ""
    match = re.search(r"@([\w.]+)", email)
    return match.group(1).lower() if match else ""


def has_free_email(text: str) -> int:
    """1 if any free email domain found in text."""
    for domain in FREE_EMAIL_DOMAINS:
        if domain in text.lower():
            return 1
    return 0


def count_spam_keywords(text: str) -> int:
    """Count how many spam/urgency keywords appear."""
    if not isinstance(text, str):
        return 0
    text_lower = text.lower()
    return sum(1 for kw in SPAM_KEYWORDS if kw in text_lower)


def uppercase_ratio(text: str) -> float:
    """Fraction of uppercase letters in text."""
    if not isinstance(text, str) or len(text) == 0:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def extract_structured_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build structured feature matrix from raw DataFrame.
    Returns a new DataFrame with numerical features only.
    """
    feats = pd.DataFrame()

    # Salary presence
    feats["has_salary"] = df["salary_range"].apply(
        lambda x: 0 if (not isinstance(x, str) or x.strip() == "") else 1
    )

    # Free / non-official email domain
    description_text = df["description"].fillna("") + " " + df["company_profile"].fillna("")
    feats["has_free_email"] = description_text.apply(has_free_email)

    # Has company website / profile
    feats["has_company_profile"] = df["company_profile"].apply(
        lambda x: 0 if (not isinstance(x, str) or len(x.strip()) < 20) else 1
    )

    # Has logo
    feats["has_logo"] = df["has_company_logo"].fillna(0).astype(int)

    # Has questions (application gateway)
    feats["has_questions"] = df["has_questions"].fillna(0).astype(int)

    # Telecommuting flag
    feats["telecommuting"] = df["telecommuting"].fillna(0).astype(int)

    # Experience requirement
    feats["has_experience_req"] = df["required_experience"].apply(
        lambda x: 0 if (not isinstance(x, str) or x.strip() == "") else 1
    )

    # Spam keyword count
    full_text = (
        df["title"].fillna("") + " " +
        df["description"].fillna("") + " " +
        df["requirements"].fillna("")
    )
    feats["spam_keyword_count"] = full_text.apply(count_spam_keywords)

    # Uppercase ratio in description
    feats["uppercase_ratio"] = df["description"].fillna("").apply(uppercase_ratio)

    # Job description length
    feats["description_length"] = df["description"].fillna("").apply(len)

    # Title length
    feats["title_length"] = df["title"].fillna("").apply(len)

    # Categorical encoding (label encode with -1 for unseen)
    label_encoders = {}
    for col in CATEGORICAL_COLUMNS:
        le = LabelEncoder()
        col_data = df[col].fillna("unknown").astype(str)
        feats[f"enc_{col}"] = le.fit_transform(col_data)
        label_encoders[col] = le

    return feats, label_encoders


# ── Main Preprocessing Pipeline ──────────────────────────────
def preprocess(save: bool = True):
    """
    Full pipeline:
    1. Load raw CSV
    2. Clean text
    3. Extract structured features
    4. Apply SMOTENC for class imbalance
    5. Split train/val/test
    6. Save processed data
    """
    logger.info("Starting preprocessing pipeline...")

    # 1. Load
    csv_path = RAW_DATA_DIR / RAW_DATASET_FILENAME
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. "
            "Download fake_job_postings.csv from Kaggle and place in data/raw/"
        )
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows. Class distribution:\n{df[TARGET_COLUMN].value_counts()}")

    # 2. Combine text
    logger.info("Cleaning and combining text fields...")
    df["combined_text"] = df.apply(combine_text_fields, axis=1)

    # 3. Structured features
    logger.info("Extracting structured features...")
    structured_df, label_encoders = extract_structured_features(df)
    labels = df[TARGET_COLUMN].values

    # 4. Scale
    scaler = StandardScaler()
    structured_scaled = scaler.fit_transform(structured_df)

    # 5. SMOTENC — identify categorical indices in structured_df
    cat_feature_names = [f"enc_{col}" for col in CATEGORICAL_COLUMNS]
    cat_indices = [
        list(structured_df.columns).index(c)
        for c in cat_feature_names
        if c in structured_df.columns
    ]
    logger.info(f"Applying SMOTENC on {structured_scaled.shape[1]} features "
                f"with {len(cat_indices)} categorical columns...")
    smote = SMOTENC(
        categorical_features=cat_indices,
        random_state=SMOTENC_RANDOM_STATE,
        k_neighbors=SMOTENC_K_NEIGHBORS,
    )
    X_resampled, y_resampled = smote.fit_resample(structured_scaled, labels)
    logger.info(
        f"After SMOTENC: {X_resampled.shape[0]} rows | "
        f"FAKE={int(y_resampled.sum())} REAL={int((y_resampled==0).sum())}"
    )

    # Text data aligned after SMOTENC (SMOTENC only affects structured; text stays original)
    # For BERT training we use the original (non-oversampled) text data with original labels
    texts = df["combined_text"].values

    # 6. Train / Val / Test split for structured data
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    # Train/Val/Test split for text (original, no SMOTE — BERT handles imbalance via weights)
    t_train, t_temp, tl_train, tl_temp = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    t_val, t_test, tl_val, tl_test = train_test_split(
        t_temp, tl_temp, test_size=0.5, random_state=42, stratify=tl_temp
    )

    if save:
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Structured data
        np.save(PROCESSED_DATA_DIR / "X_train_struct.npy", X_train)
        np.save(PROCESSED_DATA_DIR / "X_val_struct.npy", X_val)
        np.save(PROCESSED_DATA_DIR / "X_test_struct.npy", X_test)
        np.save(PROCESSED_DATA_DIR / "y_train.npy", y_train)
        np.save(PROCESSED_DATA_DIR / "y_val.npy", y_val)
        np.save(PROCESSED_DATA_DIR / "y_test.npy", y_test)

        # Text data
        np.save(PROCESSED_DATA_DIR / "t_train.npy", t_train)
        np.save(PROCESSED_DATA_DIR / "t_val.npy", t_val)
        np.save(PROCESSED_DATA_DIR / "t_test.npy", t_test)
        np.save(PROCESSED_DATA_DIR / "tl_train.npy", tl_train)
        np.save(PROCESSED_DATA_DIR / "tl_val.npy", tl_val)
        np.save(PROCESSED_DATA_DIR / "tl_test.npy", tl_test)

        # Scaler & encoders
        with open(PROCESSED_DATA_DIR / "scaler.pkl", "wb") as f:
            pickle.dump(scaler, f)
        with open(PROCESSED_DATA_DIR / "label_encoders.pkl", "wb") as f:
            pickle.dump(label_encoders, f)
        with open(PROCESSED_DATA_DIR / "feature_names.json", "w") as f:
            json.dump(list(structured_df.columns), f)

        # Save original df with combined_text for FAISS indexing
        df[["combined_text", TARGET_COLUMN]].to_parquet(
            PROCESSED_DATA_DIR / "df_for_faiss.parquet"
        )

        logger.info(f"All processed data saved to {PROCESSED_DATA_DIR}")

    return {
        "X_train": X_train, "X_val": X_val, "X_test": X_test,
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
        "t_train": t_train, "t_val": t_val, "t_test": t_test,
        "tl_train": tl_train, "tl_val": tl_val, "tl_test": tl_test,
        "scaler": scaler, "label_encoders": label_encoders,
        "feature_names": list(structured_df.columns),
    }


if __name__ == "__main__":
    preprocess(save=True)
