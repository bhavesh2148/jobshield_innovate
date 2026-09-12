# ============================================================
# api/main.py — FastAPI Backend
# ============================================================

import json
import secrets
import numpy as np
from pathlib import Path
from loguru import logger
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    JobInput, PredictResponse, ExplainResponse,
    FeedbackInput, FeedbackResponse,
    RetrainRequest, RetrainResponse,
    AdminStats, RiskLevel, RecommendationAction,
    ThreatCategory, ThreatProfileResponse,
)
from api.state import AppState

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import API_CORS_ORIGINS, ADMIN_SECRET_TOKEN


def classify_threat_severity(risk_score: int) -> tuple[RiskLevel, RecommendationAction, str]:
    """Applies Phase 0 4-Tier Security Severity Policy."""
    if risk_score >= 80:
        return (
            RiskLevel.CRITICAL,
            RecommendationAction.DO_NOT_ENGAGE,
            "CRITICAL THREAT: High probability of fraudulent recruitment or credential harvesting. Do not submit sensitive documents, financial details, or payments.",
        )
    elif risk_score >= 60:
        return (
            RiskLevel.HIGH,
            RecommendationAction.EXERCISE_CAUTION,
            "HIGH RISK: Multiple suspicious recruitment anomalies identified. Independently verify this opening on the company's verified domain before responding.",
        )
    elif risk_score >= 35:
        return (
            RiskLevel.MEDIUM,
            RecommendationAction.VERIFY_OFFICIAL_CHANNELS,
            "MEDIUM RISK: Anomalous or unverified listing indicators present. Validate recruiter identity through official corporate channels.",
        )
    else:
        return (
            RiskLevel.LOW,
            RecommendationAction.PROCEED_NORMALLY,
            "LOW RISK: No significant anomalous patterns detected. Listing characteristics align with standard authentic employment postings.",
        )


# ── Lifespan (load models once at startup) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Security pre-flight check ──────────────────────────────
    if not ADMIN_SECRET_TOKEN:
        logger.warning(
            "[SECURITY] ADMIN_SECRET_TOKEN is not set. "
            "The /retrain endpoint is DISABLED. "
            "Set ADMIN_SECRET_TOKEN in your .env file to enable it."
        )
    else:
        logger.info("[SECURITY] Admin token loaded from environment.")

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
    from security.artifact_extractor import extract_artifacts
    from security.rule_engine import evaluate_security_rules

    job_dict = job.dict()

    # 1. Raw Artifact Extraction (preserves @, :, /, $, URLs, formatting)
    raw_content = "\n".join(filter(None, [job.title, job.company, job.description, job.requirements, job.benefits]))
    artifacts = extract_artifacts(raw_content)

    # 2. Deterministic Security Rule Evaluation
    findings = evaluate_security_rules(job_dict, artifacts, raw_content)

    # Roll up findings into threat categories
    category_map: dict[str, list[str]] = {}
    for f in findings:
        cat = f.category or "GENERAL_SUSPICION"
        category_map.setdefault(cat, []).append(f.id)

    threat_categories = []
    category_titles = {
        "ADVANCE_FEE_FRAUD": ("Advance-Fee Recruitment Fraud", "CRITICAL"),
        "BRAND_IMPERSONATION": ("Corporate Brand & Identity Impersonation", "HIGH"),
        "OFF_PLATFORM_RECRUITMENT": ("Off-Platform Screening Redirection", "MEDIUM"),
        "CREDENTIAL_OR_PII_HARVESTING": ("PII & Credential Harvesting Scheme", "HIGH"),
    }
    for cat_id, finding_ids in category_map.items():
        title, def_conf = category_titles.get(cat_id, (cat_id.replace("_", " ").title(), "SUSPECTED"))
        threat_categories.append(
            ThreatCategory(
                id=cat_id,
                name=title,
                confidence=def_conf,
                description=f"Identified {len(finding_ids)} security finding(s) matching this threat pattern.",
                associated_findings=finding_ids
            )
        )

    # 3. ML Feature Extraction (BERT preprocessed text & structured features)
    combined_text = build_combined_text(job_dict)
    structured_feats = extract_features_from_input(job_dict)

    # 4. Ensemble prediction
    result = AppState.ensemble.predict_single(combined_text, structured_feats)

    # 5. FAISS similarity
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

    # 6. SHAP explanation
    reasons = AppState.explainer.explain_structured(structured_feats, top_k=5)
    human_explanation = AppState.explainer.format_human_explanation(
        reasons, result["prediction"]
    )
    highlights = highlight_suspicious_phrases(combined_text)

    # 7. Background tasks
    background_tasks.add_task(
        _background_update,
        combined_text, structured_feats,
        result["prediction"], result["confidence"], result["final_prob"],
    )

    # 8. Phase 4 Evidence & Risk Correlation
    from security.correlation_engine import correlate_signals
    correlation = correlate_signals(
        artifacts=artifacts,
        security_findings=findings,
        ml_result=result,
        similarity_info=similarity_info,
        shap_reasons=reasons,
        raw_content=raw_content
    )

    # 9. Phase 5 Threat Taxonomy Classification
    from security.taxonomy import classify_threat_profiles
    raw_profiles = classify_threat_profiles(
        security_findings=findings,
        ml_result=result,
        artifacts=artifacts,
        similarity_info=similarity_info,
    )
    taxonomy = [
        ThreatProfileResponse(
            attack_type=p.attack_type,
            profile_name=p.profile_name,
            confidence=p.confidence,
            description=p.description,
            mitre_tags=[
                {"technique_id": t.technique_id, "technique_name": t.technique_name,
                 "tactic": t.tactic, "url": t.url, "relevance": t.relevance}
                for t in p.mitre_tags
            ],
            evidence_basis=p.evidence_basis,
        )
        for p in raw_profiles
    ]

    return PredictResponse(
        risk_level=correlation.risk_level,
        risk_score=correlation.risk_score,
        confidence=result["confidence"],
        recommendation=correlation.recommendation,
        action=correlation.action,
        prediction=result["prediction"],
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
        artifacts=artifacts,
        findings=findings,
        threat_categories=threat_categories,
        unified_findings=correlation.unified_findings,
        assessment_reasons=correlation.assessment_reasons,
        taxonomy=taxonomy,
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
    risk_level, _, _ = classify_threat_severity(result["risk_score"])

    return ExplainResponse(
        risk_level=risk_level,
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        prediction=result["prediction"],
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
    # Option A: if ADMIN_SECRET_TOKEN is not configured, endpoint is disabled.
    if not ADMIN_SECRET_TOKEN:
        raise HTTPException(503, "Retraining endpoint is disabled: no admin token configured.")

    # secrets.compare_digest prevents timing attacks by always taking the
    # same amount of time regardless of where the strings differ.
    provided = req.admin_token or ""
    if not secrets.compare_digest(provided, ADMIN_SECRET_TOKEN):
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


# ── Phase 6: OCR Ingestion Endpoint ────────────────────────────
@app.post("/ocr-ingest")
async def ocr_ingest(file: UploadFile = File(...)):
    """
    Phase 6: Extract text from a job posting screenshot or image.

    Accepts PNG, JPEG, WEBP, BMP, TIFF image uploads.
    Processes locally using Tesseract OCR — no data sent externally.
    Returns the extracted text ready to be submitted to /predict.

    Returns 503 with installation instructions if Tesseract is not installed.
    """
    from ocr.engine import (
        extract_text_from_image,
        TesseractUnavailableError,
        OCRExtractionError,
        SUPPORTED_MIME_TYPES,
        get_ocr_status,
    )

    # Validate file type
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in SUPPORTED_MIME_TYPES:
        # Fallback: try to detect from extension
        ext_map = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".bmp": "image/bmp", ".tiff": "image/tiff",
            ".gif": "image/gif",
        }
        fname = (file.filename or "").lower()
        for ext, mime in ext_map.items():
            if fname.endswith(ext):
                content_type = mime
                break
        else:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": "unsupported_file_type",
                    "message": f"File type '{file.content_type}' is not supported for OCR.",
                    "supported_types": list(SUPPORTED_MIME_TYPES),
                }
            )

    # Read image bytes
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=413, detail="Image file too large. Maximum size is 20MB.")

    # Run OCR
    try:
        extracted_text = extract_text_from_image(image_bytes, content_type)
        return {
            "extracted_text": extracted_text,
            "char_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "source": "ocr",
            "filename": file.filename,
            "mime_type": content_type,
        }

    except TesseractUnavailableError as e:
        ocr_status = get_ocr_status()
        raise HTTPException(
            status_code=503,
            detail={
                "error": "tesseract_not_installed",
                "message": str(e),
                "ocr_status": ocr_status,
                "install_guide": (
                    "Windows: Download Tesseract from https://github.com/UB-Mannheim/tesseract/wiki, "
                    "then restart the JobShield API. "
                    "macOS: brew install tesseract. "
                    "Ubuntu: sudo apt install tesseract-ocr."
                )
            }
        )

    except OCRExtractionError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ocr_extraction_failed",
                "message": str(e),
                "hint": "Try uploading a higher-resolution image with clearly visible text."
            }
        )

    except Exception as e:
        logger.exception(f"Unexpected OCR error: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")


# ── GET /ocr-status ───────────────────────────────────────
@app.get("/ocr-status")
def ocr_status():
    """Returns OCR system availability and Tesseract installation status."""
    from ocr.engine import get_ocr_status
    return get_ocr_status()
