# ============================================================
# ensemble/ensemble.py — Weighted Soft Voting Ensemble
# ============================================================

import json
import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.metrics import classification_report, roc_auc_score
from scipy.optimize import minimize

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    DEFAULT_ENSEMBLE_WEIGHTS, ENSEMBLE_WEIGHTS_PATH,
    FRAUD_THRESHOLD, PROCESSED_DATA_DIR,
    BERT_MODEL_DIR, XGB_MODEL_PATH, LR_MODEL_PATH,
)


class EnsemblePredictor:
    """
    Combines BERT, XGBoost, and Logistic Regression via
    weighted soft voting:
        Final_Prob = w1*BERT + w2*XGB + w3*LR
    Weights can be tuned automatically via Nelder-Mead optimization.
    """

    def __init__(self):
        self.weights = DEFAULT_ENSEMBLE_WEIGHTS.copy()
        self.bert_model = None
        self.xgb_model = None
        self.lr_model = None
        self._load_models()

    def _load_models(self):
        """Lazy-load all three sub-models."""
        from models.bert_classifier import BERTTrainer
        from models.classical_models import XGBoostClassifier, LRClassifier

        if BERT_MODEL_DIR.exists():
            try:
                logger.info("Loading BERT model...")
                self.bert_model = BERTTrainer.load()
            except Exception as e:
                logger.warning(f"BERT model weights could not be loaded ({e}) — falling back to classical ensemble.")
                self.bert_model = None
        else:
            logger.warning("BERT model not found — BERT predictions disabled.")

        if XGB_MODEL_PATH.exists():
            logger.info("Loading XGBoost model...")
            self.xgb_model = XGBoostClassifier.load()
        else:
            logger.warning("XGBoost model not found.")

        if LR_MODEL_PATH.exists():
            logger.info("Loading LR model...")
            self.lr_model = LRClassifier.load()
        else:
            logger.warning("LR model not found.")

        if ENSEMBLE_WEIGHTS_PATH.exists():
            with open(ENSEMBLE_WEIGHTS_PATH) as f:
                self.weights = json.load(f)
            logger.info(f"Loaded ensemble weights: {self.weights}")

    def predict_proba_from_parts(
        self,
        bert_probs: np.ndarray,
        xgb_probs: np.ndarray,
        lr_probs: np.ndarray,
    ) -> np.ndarray:
        """Combine already-computed probabilities."""
        w = self.weights
        return (
            w["bert"] * bert_probs +
            w["xgb"] * xgb_probs +
            w["lr"] * lr_probs
        )

    def predict_single(
        self,
        text: str,
        structured_features: np.ndarray,
    ) -> dict:
        """
        Predict a single job posting.

        Parameters
        ----------
        text : str
            Combined cleaned text of the job posting.
        structured_features : np.ndarray
            Scaled structured feature vector (1D).

        Returns
        -------
        dict with keys: prediction, confidence, risk_score,
                        bert_prob, xgb_prob, lr_prob, final_prob
        """
        X_struct = structured_features.reshape(1, -1)

        bert_prob = self.bert_model.predict_proba([text])[0] if self.bert_model else 0.5
        xgb_prob  = self.xgb_model.predict_proba(X_struct)[0] if self.xgb_model else 0.5
        lr_prob   = self.lr_model.predict_proba(X_struct)[0] if self.lr_model else 0.5

        active_weights = {}
        total_w = 0.0
        if self.bert_model is not None:
            active_weights["bert"] = self.weights.get("bert", 0.5)
            total_w += active_weights["bert"]
        if self.xgb_model is not None:
            active_weights["xgb"] = self.weights.get("xgb", 0.35)
            total_w += active_weights["xgb"]
        if self.lr_model is not None:
            active_weights["lr"] = self.weights.get("lr", 0.15)
            total_w += active_weights["lr"]

        if total_w > 0:
            for k in active_weights:
                active_weights[k] /= total_w
        else:
            active_weights = {"xgb": 0.70, "lr": 0.30}

        final_prob = (
            active_weights.get("bert", 0.0) * bert_prob +
            active_weights.get("xgb", 0.0)  * xgb_prob +
            active_weights.get("lr", 0.0)   * lr_prob
        )

        prediction = "FAKE" if final_prob >= FRAUD_THRESHOLD else "REAL"
        confidence = final_prob if prediction == "FAKE" else (1 - final_prob)
        risk_score = int(round(final_prob * 100))

        return {
            "prediction": prediction,
            "confidence": round(float(confidence) * 100, 1),
            "risk_score": risk_score,
            "final_prob": round(float(final_prob), 4),
            "bert_prob": round(float(bert_prob), 4),
            "xgb_prob": round(float(xgb_prob), 4),
            "lr_prob": round(float(lr_prob), 4),
        }

    def predict_batch(self, texts: list, X_struct: np.ndarray) -> np.ndarray:
        """Return final_prob for a batch."""
        bert_probs = self.bert_model.predict_proba(texts) if self.bert_model else np.full(len(texts), 0.5)
        xgb_probs  = self.xgb_model.predict_proba(X_struct) if self.xgb_model else np.full(len(texts), 0.5)
        lr_probs   = self.lr_model.predict_proba(X_struct) if self.lr_model else np.full(len(texts), 0.5)
        return self.predict_proba_from_parts(bert_probs, xgb_probs, lr_probs)

    # ── Weight Tuning ─────────────────────────────────────────
    def tune_weights(self, texts_val, X_val, y_val):
        """
        Optimize ensemble weights on validation set using
        Nelder-Mead to maximize AUC-PR for FAKE class.
        """
        logger.info("Computing base predictions for weight tuning...")
        bert_probs = self.bert_model.predict_proba(texts_val) if self.bert_model else np.full(len(texts_val), 0.5)
        xgb_probs  = self.xgb_model.predict_proba(X_val) if self.xgb_model else np.full(len(texts_val), 0.5)
        lr_probs   = self.lr_model.predict_proba(X_val) if self.lr_model else np.full(len(texts_val), 0.5)

        # sometimes structured validation (after SMOTE) is longer than text validation
        # slice all arrays down to the smallest length to avoid broadcasting errors
        lengths = [len(bert_probs), len(xgb_probs), len(lr_probs), len(y_val)]
        if len(set(lengths)) != 1:
            minlen = min(lengths)
            logger.warning(
                "Validation set lengths differ (%s); truncating to %d samples",
                lengths, minlen,
            )
            bert_probs = bert_probs[:minlen]
            xgb_probs  = xgb_probs[:minlen]
            lr_probs   = lr_probs[:minlen]
            y_val      = y_val[:minlen]

        def neg_auc(w):
            w = np.array(w)
            w = np.clip(w, 0, 1)
            w = w / w.sum()  # normalize to sum=1
            combined = w[0]*bert_probs + w[1]*xgb_probs + w[2]*lr_probs
            return -roc_auc_score(y_val, combined)

        result = minimize(
            neg_auc,
            x0=[0.5, 0.35, 0.15],
            method="Nelder-Mead",
            options={"maxiter": 1000, "xatol": 1e-4},
        )

        best_w = np.clip(result.x, 0, 1)
        best_w = best_w / best_w.sum()

        self.weights = {
            "bert": round(float(best_w[0]), 4),
            "xgb":  round(float(best_w[1]), 4),
            "lr":   round(float(best_w[2]), 4),
        }

        ENSEMBLE_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ENSEMBLE_WEIGHTS_PATH, "w") as f:
            json.dump(self.weights, f, indent=2)

        # Final eval
        final_probs = best_w[0]*bert_probs + best_w[1]*xgb_probs + best_w[2]*lr_probs
        preds = (final_probs >= FRAUD_THRESHOLD).astype(int)
        auc = roc_auc_score(y_val, final_probs)
        logger.info(f"Tuned weights: {self.weights}")
        logger.info(f"Ensemble Val AUC: {auc:.4f}")
        logger.info(classification_report(y_val, preds))

        return self.weights


# ── Tuning Entry Point ───────────────────────────────────────
if __name__ == "__main__":
    import numpy as np
    ensemble = EnsemblePredictor()

    t_val  = np.load(PROCESSED_DATA_DIR / "t_val.npy", allow_pickle=True)
    X_val  = np.load(PROCESSED_DATA_DIR / "X_val_struct.npy")
    tl_val = np.load(PROCESSED_DATA_DIR / "tl_val.npy")

    ensemble.tune_weights(list(t_val), X_val, tl_val)
