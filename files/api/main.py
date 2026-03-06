# ============================================================
# api/main.py — FastAPI Backend
# ============================================================

import json
import numpy as np
from pathlib import Path
from loguru import logger
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    JobInput, PredictResponse, ExplainResponse,
    FeedbackInput, FeedbackResponse,
    RetrainRequest, RetrainResponse,
    AdminStats,
)
from api.state import AppState

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import API_CORS_ORIGINS


# ── Lifespan (load models once at startup) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading models and indexes...")
    AppState.init()
    logger.info("All models ready.")
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="Fake Job Detection API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "models_loaded": AppState.ready}


# ── POST /predict ─────────────────────────────────────────────
@app.post("/predict", response_model=PredictResponse)
async def predict(job: JobInput, background_tasks: BackgroundTasks):
    """
    Full prediction pipeline:
    1. Feature extraction
    2. Ensemble prediction
    3. FAISS similarity check
    4. SHAP explanation
    5. Self-training accumulation
    6. Drift monitoring
    """
    if not AppState.ready:
        raise HTTPException(503, "Models not loaded yet")

    from utils.feature_extractor import extract_features_from_input, build_combined_text
    from explainability.explainer import highlight_suspicious_phrases

    job_dict = job.dict()

    # 1. Feature extraction
    combined_text = build_combined_text(job_dict)
    structured_feats = extract_features_from_input(job_dict)

    # 2. Ensemble prediction
    result = AppState.ensemble.predict_single(combined_text, structured_feats)

    # 3. FAISS similarity
    similarity_info = AppState.faiss_store.similarity_boost(combined_text)
    if similarity_info["boosted"]:
        # Nudge final_prob upward when similar to known fake
        boosted_prob = min(1.0, result["final_prob"] + 0.10)
        result["final_prob"] = round(boosted_prob, 4)
        result["risk_score"] = int(round(boosted_prob * 100))
        if boosted_prob >= 0.5:
            result["prediction"] = "FAKE"
        conf = boosted_prob if result["prediction"] == "FAKE" else (1 - boosted_prob)
        result["confidence"] = round(conf * 100, 1)

    # 4. SHAP explanation
    reasons = AppState.explainer.explain_structured(structured_feats, top_k=5)
    human_explanation = AppState.explainer.format_human_explanation(
        reasons, result["prediction"]
    )
    highlights = highlight_suspicious_phrases(combined_text)

    # 5–6. Background tasks
    background_tasks.add_task(
        _background_update,
        combined_text, structured_feats,
        result["prediction"], result["confidence"], result["final_prob"],
    )

    return PredictResponse(
        prediction=result["prediction"],
        confidence=result["confidence"],
        risk_score=result["risk_score"],
        final_prob=result["final_prob"],
        bert_prob=result["bert_prob"],
        xgb_prob=result["xgb_prob"],
        lr_prob=result["lr_prob"],
        explanation=reasons,
        human_explanation=human_explanation,
        highlights=highlights,
        similarity_score=similarity_info["similarity_score"],
        similarity_message=similarity_info["message"],
        top_match_snippet=similarity_info["top_match_snippet"],
    )


# ── POST /explain ─────────────────────────────────────────────
@app.post("/explain", response_model=ExplainResponse)
async def explain(job: JobInput):
    """Detailed SHAP explanation for a job posting."""
    if not AppState.ready:
        raise HTTPException(503, "Models not loaded yet")

    from utils.feature_extractor import extract_features_from_input, build_combined_text
    job_dict = job.dict()
    combined_text = build_combined_text(job_dict)
    structured_feats = extract_features_from_input(job_dict)
    result = AppState.ensemble.predict_single(combined_text, structured_feats)
    reasons = AppState.explainer.explain_structured(structured_feats, top_k=10)
    human_explanation = AppState.explainer.format_human_explanation(
        reasons, result["prediction"]
    )
    return ExplainResponse(
        prediction=result["prediction"],
        confidence=result["confidence"],
        risk_score=result["risk_score"],
        explanation=reasons,
        human_explanation=human_explanation,
    )


# ── POST /feedback ────────────────────────────────────────────
@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(fb: FeedbackInput, background_tasks: BackgroundTasks):
    """Record user-reported incorrect prediction."""
    AppState.feedback_store.append(fb.dict())
    logger.info(f"Feedback received: {fb.dict()}")
    background_tasks.add_task(_save_feedback)
    return FeedbackResponse(
        message="Thank you for your feedback! It will help improve the system.",
        received=True,
    )


# ── POST /retrain ─────────────────────────────────────────────
@app.post("/retrain", response_model=RetrainResponse)
async def retrain(req: RetrainRequest, background_tasks: BackgroundTasks):
    """Admin: trigger model retraining."""
    if not req.admin_token or req.admin_token != "admin-secret-2024":
        raise HTTPException(403, "Invalid admin token")

    background_tasks.add_task(_run_retrain, req.admin_approved)
    return RetrainResponse(
        message="Retraining scheduled in background.",
        scheduled=True,
    )


# ── GET /admin/stats ──────────────────────────────────────────
@app.get("/admin/stats", response_model=AdminStats)
def admin_stats():
    """Admin dashboard data."""
    drift_events = AppState.drift_detector.drift_events
    return AdminStats(
        total_predictions=AppState.drift_detector.total_predictions,
        pseudo_label_count=AppState.self_trainer.total_count,
        pending_validation=AppState.self_trainer.pending_count,
        retrain_needed=AppState.self_trainer.retrain_needed(),
        drift_detected=len(drift_events) > 0,
        drift_events=drift_events[-10:],
        feedback_count=len(AppState.feedback_store),
    )


# ── Background Helpers ────────────────────────────────────────
def _background_update(text, structured_feats, prediction, confidence, prob):
    AppState.self_trainer.maybe_add_pseudo_label(
        text, structured_feats, prediction, confidence
    )
    AppState.drift_detector.update(prob)


def _save_feedback():
    feedback_path = Path("data/feedback.json")
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    with open(feedback_path, "w") as f:
        json.dump(AppState.feedback_store, f, indent=2)


def _run_retrain(admin_approved: bool):
    AppState.self_trainer.validate_and_retrain(admin_approved)
