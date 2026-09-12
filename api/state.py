# ============================================================
# api/state.py — Singleton model/service registry
# ============================================================

from loguru import logger
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))


class AppState:
    """
    Holds all loaded model instances.
    Call AppState.init() once at startup.
    """
    ready: bool = False
    ensemble = None
    explainer = None
    faiss_store = None
    drift_detector = None
    self_trainer = None
    feedback_store: list = []

    @classmethod
    def init(cls):
        try:
            from ensemble.ensemble import EnsemblePredictor
            from explainability.explainer import Explainer
            from memory.faiss_store import FAISSMemoryStore
            from drift_detection.detector import DriftDetector
            from self_training.self_trainer import SelfTrainer
            from config.settings import XGB_MODEL_PATH

            import json
            from config.settings import PROCESSED_DATA_DIR

            cls.ensemble = EnsemblePredictor()
            cls.faiss_store = FAISSMemoryStore()
            cls.drift_detector = DriftDetector()
            cls.self_trainer = SelfTrainer()
            cls.feedback_store = []

            # Build explainer (needs XGBoost model + feature names)
            if XGB_MODEL_PATH.exists():
                from models.classical_models import XGBoostClassifier
                fn_path = PROCESSED_DATA_DIR / "feature_names.json"
                if fn_path.exists():
                    with open(fn_path) as f:
                        feature_names = json.load(f)
                else:
                    feature_names = [f"f{i}" for i in range(20)]
                xgb_model = XGBoostClassifier.load()
                cls.explainer = Explainer(xgb_model, feature_names)
            else:
                logger.warning("XGBoost not found — explainer disabled.")
                cls.explainer = None

            cls.ready = True
            logger.info("AppState initialized successfully.")

        except Exception as e:
            logger.error(f"AppState init failed: {e}")
            cls.ready = False
            raise
