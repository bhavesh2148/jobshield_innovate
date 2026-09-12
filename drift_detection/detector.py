# ============================================================
# drift_detection/detector.py — ADWIN-based drift detection
# ============================================================

import json
import pickle
from pathlib import Path
from loguru import logger
from river.drift import ADWIN

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import ADWIN_DELTA, DRIFT_CHECK_INTERVAL, BASE_DIR

DETECTOR_STATE_PATH = BASE_DIR / "drift_detection" / "adwin_state.pkl"
DRIFT_LOG_PATH = BASE_DIR / "drift_detection" / "drift_events.json"


class DriftDetector:
    """
    ADWIN (ADaptive WINdowing) drift detector.
    Monitors the stream of prediction probabilities.
    When the distribution shifts significantly, alerts admin.
    """

    def __init__(self):
        self.detector = ADWIN(delta=ADWIN_DELTA)
        self._n_predictions = 0
        self._drift_events: list[dict] = []
        self._load_state()

    # ── Persistence ───────────────────────────────────────────
    def _load_state(self):
        if DETECTOR_STATE_PATH.exists():
            with open(DETECTOR_STATE_PATH, "rb") as f:
                state = pickle.load(f)
                self.detector = state.get("detector", ADWIN(delta=ADWIN_DELTA))
                self._n_predictions = state.get("n_predictions", 0)
                self._drift_events = state.get("drift_events", [])
            logger.info(f"Drift detector loaded. {self._n_predictions} predictions seen.")
        if DRIFT_LOG_PATH.exists():
            with open(DRIFT_LOG_PATH) as f:
                self._drift_events = json.load(f)

    def _save_state(self):
        DETECTOR_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DETECTOR_STATE_PATH, "wb") as f:
            pickle.dump({
                "detector": self.detector,
                "n_predictions": self._n_predictions,
                "drift_events": self._drift_events,
            }, f)

    # ── Core API ──────────────────────────────────────────────
    def update(self, prediction_prob: float) -> bool:
        """
        Feed a new prediction probability to the detector.

        Returns True if drift is detected, False otherwise.
        """
        self._n_predictions += 1
        self.detector.update(prediction_prob)

        if self.detector.drift_detected:
            import datetime
            event = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "n_predictions_at_drift": self._n_predictions,
                "message": "ADWIN detected distribution shift in prediction stream",
            }
            self._drift_events.append(event)
            logger.warning(f"⚠ DRIFT DETECTED at prediction #{self._n_predictions}")

            # Persist
            DRIFT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DRIFT_LOG_PATH, "w") as f:
                json.dump(self._drift_events[-100:], f, indent=2)  # keep last 100

            self._save_state()

            # Reset ADWIN window after drift
            self.detector = ADWIN(delta=ADWIN_DELTA)
            return True

        # Checkpoint every N predictions
        if self._n_predictions % DRIFT_CHECK_INTERVAL == 0:
            self._save_state()

        return False

    @property
    def total_predictions(self) -> int:
        return self._n_predictions

    @property
    def drift_events(self) -> list[dict]:
        return self._drift_events

    @property
    def drift_detected(self) -> bool:
        return len(self._drift_events) > 0
