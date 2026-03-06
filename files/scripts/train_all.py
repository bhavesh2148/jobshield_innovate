#!/usr/bin/env python3
# scripts/train_all.py
# ============================================================
# Master training script — runs the full pipeline in order.
# ============================================================

import subprocess
import sys
from pathlib import Path
from loguru import logger

# make sure top-level package (files/) is on path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# also load settings path for the bert model
from config.settings import BERT_MODEL_DIR

STEPS = [
    ("Preprocess data",           "data/preprocessor.py"),
    ("Train BERT classifier",     "models/bert_classifier.py"),
    ("Train XGBoost + LR",        "models/classical_models.py"),
    ("Tune ensemble weights",     "ensemble/ensemble.py"),
    ("Build FAISS index",         "memory/faiss_store.py"),
]

def run(script: str):
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        logger.error(f"❌ Failed: {script}")
        sys.exit(1)
    logger.success(f"✓ Completed: {script}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  Fake Job Detector — Full Training Pipeline")
    logger.info("=" * 60)

    for label, script in STEPS:
        # skip training BERT if model directory already exists with saved weights
        if "BERT" in label and Path(BERT_MODEL_DIR).exists():
            logger.info(f"⚠️  {label} step skipped (model already present at {BERT_MODEL_DIR})")
            continue

        logger.info(f"\n{'─'*50}\n▶ {label}\n{'─'*50}")
        run(script)

    logger.success("\n🎉 All training steps complete! Start the API with:\n"
                   "   uvicorn api.main:app --reload --port 8000")
