# ============================================================
# config/settings.py — Central configuration for all modules
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level above this file).
# This is a no-op if .env doesn't exist — the file is optional;
# production environments inject variables directly into os.environ.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ── Paths ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PSEUDO_LABEL_DIR = DATA_DIR / "pseudo_labeled"
MODELS_DIR = BASE_DIR / "models"
BERT_MODEL_DIR = MODELS_DIR / "bert"
XGB_MODEL_PATH = MODELS_DIR / "xgboost" / "xgb_model.pkl"
LR_MODEL_PATH = MODELS_DIR / "logistic" / "lr_model.pkl"
SCALER_PATH = PROCESSED_DATA_DIR / "scaler.pkl"
ENSEMBLE_WEIGHTS_PATH = MODELS_DIR / "ensemble_weights.json"
FAISS_INDEX_PATH = BASE_DIR / "memory" / "faiss_index.bin"
FAISS_METADATA_PATH = BASE_DIR / "memory" / "faiss_metadata.pkl"

# ── Dataset ─────────────────────────────────────────────────
RAW_DATASET_FILENAME = "fake_job_postings.csv"
TARGET_COLUMN = "fraudulent"
TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]
CATEGORICAL_COLUMNS = ["employment_type", "required_experience", "required_education",
                        "industry", "function"]

# ── BERT / RoBERTa ──────────────────────────────────────────
BERT_MODEL_NAME = "distilbert-base-uncased"   # Swap to "roberta-base" for higher accuracy
BERT_MAX_LENGTH = 256
BERT_BATCH_SIZE = 16
BERT_EPOCHS = 1
BERT_LEARNING_RATE = 2e-5
BERT_WARMUP_RATIO = 0.1

# ── SBERT (Memory / Similarity) ─────────────────────────────
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.85   # Above this → boost fraud probability

# ── Ensemble Weights (defaults, tuned via CV) ───────────────
DEFAULT_ENSEMBLE_WEIGHTS = {
    "bert": 0.50,
    "xgb":  0.35,
    "lr":   0.15,
}

# ── Classification Threshold ────────────────────────────────
FRAUD_THRESHOLD = 0.50        # Prob above this → FAKE
HIGH_CONFIDENCE_THRESHOLD = 0.95  # For self-training pseudo-labels

# ── SMOTENC ─────────────────────────────────────────────────
SMOTENC_RANDOM_STATE = 42
SMOTENC_K_NEIGHBORS = 5

# ── Drift Detection ─────────────────────────────────────────
ADWIN_DELTA = 0.002           # Sensitivity (lower = more sensitive)
DRIFT_CHECK_INTERVAL = 100    # Check every N predictions

# ── Self-Training ───────────────────────────────────────────
PSEUDO_LABEL_MIN_SAMPLES = 50   # Min new samples before retraining
RETRAIN_SCHEDULE_HOURS = 24     # Periodic retrain interval

# ── Spam / Urgency Keywords ─────────────────────────────────
SPAM_KEYWORDS = [
    "urgent", "immediately", "work from home", "earn up to",
    "no experience needed", "make money fast", "guaranteed",
    "apply now", "limited time", "risk free", "wire transfer",
    "western union", "money order", "investment required",
    "be your own boss", "financial freedom", "passive income",
]

# ── Suspicious Email Domains ────────────────────────────────
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "mail.com", "protonmail.com", "yandex.com",
    "inbox.com", "icloud.com",
}

# ── API ─────────────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
API_CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

# ── Security ─────────────────────────────────────────────────
# Loaded from .env — never hardcoded here.
# If ADMIN_SECRET_TOKEN is not set, the /retrain endpoint will
# always reject requests (Option A: disabled when no secret).
ADMIN_SECRET_TOKEN: str = os.getenv("ADMIN_SECRET_TOKEN", "")

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "logs" / "system.log"
