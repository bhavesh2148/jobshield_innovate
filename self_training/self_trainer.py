# ============================================================
# self_training/self_trainer.py — Pseudo-label & retrain
# ============================================================

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from datetime import datetime, timezone

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    HIGH_CONFIDENCE_THRESHOLD, PSEUDO_LABEL_DIR,
    PSEUDO_LABEL_MIN_SAMPLES, PROCESSED_DATA_DIR,
)

PSEUDO_LOG_PATH = PSEUDO_LABEL_DIR / "pseudo_log.json"
PENDING_RETRAIN_FLAG = PSEUDO_LABEL_DIR / ".retrain_needed"


class SelfTrainer:
    """
    Self-training module:
    1. Collects high-confidence predictions as pseudo-labels.
    2. Triggers retraining when enough new samples accumulate.
    3. Supports admin validation before incorporating new data.
    """

    def __init__(self):
        PSEUDO_LABEL_DIR.mkdir(parents=True, exist_ok=True)
        self._pseudo_samples: list[dict] = []
        self._load_log()

    def _load_log(self):
        if PSEUDO_LOG_PATH.exists():
            with open(PSEUDO_LOG_PATH) as f:
                self._pseudo_samples = json.load(f)
            logger.info(f"Self-trainer: {len(self._pseudo_samples)} pseudo-labeled samples in log.")

    def _save_log(self):
        with open(PSEUDO_LOG_PATH, "w") as f:
            json.dump(self._pseudo_samples[-5000:], f, indent=2)  # cap at 5000

    def maybe_add_pseudo_label(
        self,
        text: str,
        structured_features: np.ndarray,
        prediction: str,
        confidence: float,
    ) -> bool:
        """
        If confidence >= HIGH_CONFIDENCE_THRESHOLD, add as pseudo-label.

        Returns True if sample was added.
        """
        if confidence / 100.0 < HIGH_CONFIDENCE_THRESHOLD:
            return False

        sample = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text_snippet": text[:300],
            "label": 1 if prediction == "FAKE" else 0,
            "confidence": confidence,
            "validated": False,  # awaits admin validation
        }
        self._pseudo_samples.append(sample)
        self._save_log()

        # Store structured features separately
        feats_path = PSEUDO_LABEL_DIR / "pending_features.npy"
        if feats_path.exists():
            existing = np.load(feats_path)
            combined = np.vstack([existing, structured_features.reshape(1, -1)])
        else:
            combined = structured_features.reshape(1, -1)
        np.save(feats_path, combined)

        # Check if retraining should be triggered
        pending_count = sum(1 for s in self._pseudo_samples if not s.get("validated", False))
        if pending_count >= PSEUDO_LABEL_MIN_SAMPLES:
            PENDING_RETRAIN_FLAG.touch()
            logger.info(
                f"✓ {pending_count} pseudo-labeled samples ready — "
                "retraining flag set (admin validation required)."
            )

        return True

    def retrain_needed(self) -> bool:
        return PENDING_RETRAIN_FLAG.exists()

    def validate_and_retrain(self, admin_approved: bool = True):
        """
        Admin approves pseudo-labeled data, triggers retraining.
        In production this would be a manual review step.
        """
        if not admin_approved:
            logger.info("Admin rejected retraining — clearing flag.")
            if PENDING_RETRAIN_FLAG.exists():
                PENDING_RETRAIN_FLAG.unlink()
            return

        validated_samples = [
            s for s in self._pseudo_samples if not s.get("validated", False)
        ]

        # Mark as validated
        for s in validated_samples:
            s["validated"] = True
        self._save_log()

        logger.info(f"Admin approved {len(validated_samples)} pseudo-labels for retraining.")

        # Import and run training scripts
        try:
            import subprocess, sys
            scripts = [
                "scripts/train_all.py",
                "scripts/evaluate.py",
            ]
            for script in scripts:
                logger.info(f"Running {script}...")
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"{script} failed:\n{result.stderr}")
                else:
                    logger.info(f"{script} completed.")
        except Exception as e:
            logger.error(f"Retraining error: {e}")

        if PENDING_RETRAIN_FLAG.exists():
            PENDING_RETRAIN_FLAG.unlink()

    @property
    def pending_count(self) -> int:
        return sum(1 for s in self._pseudo_samples if not s.get("validated", False))

    @property
    def total_count(self) -> int:
        return len(self._pseudo_samples)
