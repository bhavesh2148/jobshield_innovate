# ============================================================
# api/schemas.py — Pydantic request/response models
# ============================================================

from typing import Optional
from pydantic import BaseModel, Field


# ── Input ─────────────────────────────────────────────────────
class JobInput(BaseModel):
    title: str = Field("", description="Job title")
    company: Optional[str] = ""
    description: str = Field(..., description="Full job description")
    requirements: Optional[str] = ""
    benefits: Optional[str] = ""
    company_profile: Optional[str] = ""
    salary_range: Optional[str] = ""
    employment_type: Optional[str] = ""
    required_experience: Optional[str] = ""
    required_education: Optional[str] = ""
    industry: Optional[str] = ""
    function: Optional[str] = ""
    telecommuting: Optional[int] = 0
    has_company_logo: Optional[int] = 0
    has_questions: Optional[int] = 0


# ── Feature explanation entry ─────────────────────────────────
class FeatureReason(BaseModel):
    feature: str
    label: str
    value: float
    shap_value: float
    direction: str
    message: str
    is_risk: bool


# ── Highlight span ────────────────────────────────────────────
class Highlight(BaseModel):
    phrase: str
    start: int
    end: int


# ── Responses ─────────────────────────────────────────────────
class PredictResponse(BaseModel):
    prediction: str                         # "FAKE" | "REAL"
    confidence: float                       # 0–100 %
    risk_score: int                         # 0–100
    final_prob: float
    bert_prob: float
    xgb_prob: float
    lr_prob: float
    explanation: list[FeatureReason]
    human_explanation: str
    highlights: list[Highlight]
    similarity_score: float
    similarity_message: str
    top_match_snippet: str


class ExplainResponse(BaseModel):
    prediction: str
    confidence: float
    risk_score: int
    explanation: list[FeatureReason]
    human_explanation: str


class FeedbackInput(BaseModel):
    job_title: Optional[str] = ""
    reported_prediction: str          # What user got
    correct_label: str                # What user says it should be
    comment: Optional[str] = ""


class FeedbackResponse(BaseModel):
    message: str
    received: bool


class RetrainRequest(BaseModel):
    admin_token: str
    admin_approved: bool = True


class RetrainResponse(BaseModel):
    message: str
    scheduled: bool


class DriftEvent(BaseModel):
    timestamp: str
    n_predictions_at_drift: int
    message: str


class AdminStats(BaseModel):
    total_predictions: int
    pseudo_label_count: int
    pending_validation: int
    retrain_needed: bool
    drift_detected: bool
    drift_events: list[dict]
    feedback_count: int
