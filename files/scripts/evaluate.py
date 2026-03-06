#!/usr/bin/env python3
# scripts/evaluate.py
# ============================================================
# Evaluate the full ensemble on the held-out test set.
# ============================================================

import numpy as np
from loguru import logger
from pathlib import Path
from sklearn.metrics import (
    classification_report, roc_auc_score,
    average_precision_score, confusion_matrix,
)

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import PROCESSED_DATA_DIR, FRAUD_THRESHOLD
from ensemble.ensemble import EnsemblePredictor


def evaluate():
    logger.info("Loading test data...")
    X_test  = np.load(PROCESSED_DATA_DIR / "X_test_struct.npy")
    y_test  = np.load(PROCESSED_DATA_DIR / "y_test.npy")
    t_test  = np.load(PROCESSED_DATA_DIR / "t_test.npy", allow_pickle=True)
    tl_test = np.load(PROCESSED_DATA_DIR / "tl_test.npy")

    logger.info("Loading ensemble...")
    ensemble = EnsemblePredictor()

    logger.info("Running batch predictions...")
    probs = ensemble.predict_batch(list(t_test), X_test)
    preds = (probs >= FRAUD_THRESHOLD).astype(int)

    # ── Metrics ───────────────────────────────────────────────
    auc_roc = roc_auc_score(y_test, probs)
    auc_pr  = average_precision_score(y_test, probs)
    cm      = confusion_matrix(y_test, preds)

    logger.info("\n" + "="*60)
    logger.info("  ENSEMBLE TEST SET EVALUATION")
    logger.info("="*60)
    logger.info(f"\nROC-AUC:  {auc_roc:.4f}")
    logger.info(f"PR-AUC:   {auc_pr:.4f}")
    logger.info(f"\nConfusion Matrix:\n{cm}")
    logger.info(f"\n{classification_report(y_test, preds, target_names=['REAL', 'FAKE'])}")
    logger.info("="*60)

    # ── Per-model breakdown ───────────────────────────────────
    for name, proba in [
        ("BERT",    ensemble.bert_model.predict_proba(list(t_test)) if ensemble.bert_model else None),
        ("XGBoost", ensemble.xgb_model.predict_proba(X_test) if ensemble.xgb_model else None),
        ("LogReg",  ensemble.lr_model.predict_proba(X_test) if ensemble.lr_model else None),
    ]:
        if proba is not None:
            sub_preds = (proba >= FRAUD_THRESHOLD).astype(int)
            sub_auc = roc_auc_score(y_test, proba)
            logger.info(f"\n{name} | AUC: {sub_auc:.4f}")
            logger.info(classification_report(y_test, sub_preds, target_names=["REAL", "FAKE"]))


if __name__ == "__main__":
    evaluate()
