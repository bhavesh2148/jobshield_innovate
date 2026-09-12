# ============================================================
# models/classical_models.py — XGBoost + Logistic Regression
# ============================================================

import pickle
import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_score
import xgboost as xgb

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    PROCESSED_DATA_DIR, XGB_MODEL_PATH, LR_MODEL_PATH, SCALER_PATH
)


# ── XGBoost ──────────────────────────────────────────────────
class XGBoostClassifier:
    """
    XGBoost trained on structured features.
    Uses scale_pos_weight to handle class imbalance natively.
    """
    def __init__(self):
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        n_real = int((y_train == 0).sum())
        n_fake = int((y_train == 1).sum())
        scale = n_real / n_fake
        logger.info(f"XGBoost scale_pos_weight = {scale:.2f}")

        self.model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale,
            eval_metric="aucpr",
            early_stopping_rounds=30,
            random_state=42,
            n_jobs=-1,
            tree_method="hist",  # fast, CPU-friendly
        )
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=50,
        )

        val_probs = self.model.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= 0.5).astype(int)
        auc = roc_auc_score(y_val, val_probs)
        logger.info(f"XGBoost Val AUC: {auc:.4f}")
        logger.info(classification_report(y_val, val_preds))

        self.save()

    def save(self):
        XGB_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(XGB_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"XGBoost saved to {XGB_MODEL_PATH}")

    @classmethod
    def load(cls):
        inst = cls()
        with open(XGB_MODEL_PATH, "rb") as f:
            inst.model = pickle.load(f)
        return inst

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def feature_importances(self) -> dict:
        return dict(enumerate(self.model.feature_importances_))


# ── Logistic Regression ──────────────────────────────────────
class LRClassifier:
    """
    Logistic Regression as baseline stabilizer.
    Works on scaled structured features.
    """
    def __init__(self):
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        self.model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            C=1.0,
            solver="lbfgs",
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        val_probs = self.model.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= 0.5).astype(int)
        auc = roc_auc_score(y_val, val_probs)
        logger.info(f"LogReg Val AUC: {auc:.4f}")
        logger.info(classification_report(y_val, val_preds))

        # 5-fold CV
        cv_scores = cross_val_score(
            self.model, X_train, y_train, cv=5, scoring="roc_auc"
        )
        logger.info(f"LogReg 5-fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        self.save()

    def save(self):
        LR_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LR_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"LR saved to {LR_MODEL_PATH}")

    @classmethod
    def load(cls):
        inst = cls()
        with open(LR_MODEL_PATH, "rb") as f:
            inst.model = pickle.load(f)
        return inst

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]


# ── Training Entry Point ─────────────────────────────────────
if __name__ == "__main__":
    X_train = np.load(PROCESSED_DATA_DIR / "X_train_struct.npy")
    X_val   = np.load(PROCESSED_DATA_DIR / "X_val_struct.npy")
    y_train = np.load(PROCESSED_DATA_DIR / "y_train.npy")
    y_val   = np.load(PROCESSED_DATA_DIR / "y_val.npy")

    logger.info("=== Training XGBoost ===")
    xgb_clf = XGBoostClassifier()
    xgb_clf.train(X_train, y_train, X_val, y_val)

    logger.info("=== Training Logistic Regression ===")
    lr_clf = LRClassifier()
    lr_clf.train(X_train, y_train, X_val, y_val)
