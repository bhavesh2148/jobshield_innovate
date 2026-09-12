# ============================================================
# api/schemas.py — Pydantic request/response models
# ============================================================

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ── Threat Intelligence Semantics ─────────────────────────────
class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationAction(str, Enum):
    PROCEED_NORMALLY = "PROCEED_NORMALLY"
    VERIFY_OFFICIAL_CHANNELS = "VERIFY_OFFICIAL_CHANNELS"
    EXERCISE_CAUTION = "EXERCISE_CAUTION"
    DO_NOT_ENGAGE = "DO_NOT_ENGAGE"


# ── Security Artifact Extraction Schemas ──────────────────────
class ArtifactType(str, Enum):
    EMAIL = "EMAIL"
    URL = "URL"
    DOMAIN = "DOMAIN"
    PHONE = "PHONE"
    PAYMENT_IDENTIFIER = "PAYMENT_IDENTIFIER"


class ExtractedArtifact(BaseModel):
    type: ArtifactType
    value: str                          # Canonical normalized form: "recruiter@gmail.com"
    raw: str                            # Verbatim substring from input text
    domain: Optional[str] = None        # Hostname/domain if applicable
    start: int                          # Start character index in source text
    end: int                            # End character index in source text
    metadata: dict[str, str] = Field(default_factory=dict)


class ArtifactReport(BaseModel):
    emails: list[ExtractedArtifact] = Field(default_factory=list)
    urls: list[ExtractedArtifact] = Field(default_factory=list)
    domains: list[ExtractedArtifact] = Field(default_factory=list)
    phones: list[ExtractedArtifact] = Field(default_factory=list)
    payment_identifiers: list[ExtractedArtifact] = Field(default_factory=list)
    total_count: int = 0


# ── Security Rule Findings & Threat Categories ────────────────
class RuleSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityFinding(BaseModel):
    id: str                             # e.g. "FINDING-PAYMENT-SOLICITATION"
    rule_id: str                        # e.g. "RULE_ADVANCE_FEE_PAYMENT"
    title: str                          # Human-readable title
    severity: RuleSeverity              # INFO, LOW, MEDIUM, HIGH, CRITICAL
    description: str                    # Concise factual explanation of finding
    evidence_value: Optional[str] = None # Relevant artifact value or string that triggered the rule
    category: Optional[str] = None      # Target threat category


class ThreatCategory(BaseModel):
    id: str                             # e.g. "ADVANCE_FEE_FRAUD"
    name: str                           # e.g. "Advance-Fee Recruitment Scam"
    confidence: str                     # "CONFIRMED" | "PROBABLE" | "SUSPECTED"
    description: str                    # Explanation of threat type
    associated_findings: list[str] = Field(default_factory=list) # List of finding IDs that formed this category


# ── MITRE ATT&CK Taxonomy Schemas (Phase 5) ──────────────────
class MitreTechniqueTag(BaseModel):
    technique_id: str                   # e.g. "T1657"
    technique_name: str                 # e.g. "Financial Theft"
    tactic: str                         # e.g. "Impact"
    url: str                            # https://attack.mitre.org/techniques/T1657/
    relevance: str                      # "HIGH" | "MEDIUM" | "LOW"


class ThreatProfileResponse(BaseModel):
    attack_type: str                    # e.g. "ADVANCE_FEE_FRAUD"
    profile_name: str                   # e.g. "Advance-Fee Recruitment Fraud"
    confidence: str                     # "CONFIRMED" | "PROBABLE" | "SUSPECTED"
    description: str                    # Analyst-facing explanation
    mitre_tags: list[MitreTechniqueTag] = Field(default_factory=list)
    evidence_basis: list[str] = Field(default_factory=list)


# ── Unified Evidence & Correlation Schemas ─────────────────────
class EvidenceSource(str, Enum):
    RULE_ENGINE = "RULE_ENGINE"
    ML_MODEL = "ML_MODEL"
    VECTOR_MEMORY = "VECTOR_MEMORY"
    COMPOUND_CORRELATION = "COMPOUND_CORRELATION"


class FindingType(str, Enum):
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    MODEL_INDICATOR = "MODEL_INDICATOR"
    SIMILARITY_MATCH = "SIMILARITY_MATCH"
    COMPOUND_SIGNAL = "COMPOUND_SIGNAL"


class UnifiedFinding(BaseModel):
    id: str
    source: EvidenceSource
    finding_type: FindingType
    severity: RuleSeverity
    title: str
    description: str
    evidence_value: Optional[str] = None
    supporting_artifacts: list[str] = Field(default_factory=list)
    category: Optional[str] = None



# ── Input with Boundary Validation ────────────────────────────
class JobInput(BaseModel):
    title: str = Field("", max_length=200, description="Job title")
    company: Optional[str] = Field("", max_length=150, description="Company or organization name")
    description: str = Field(..., min_length=20, max_length=15000, description="Full job description")
    requirements: Optional[str] = Field("", max_length=5000, description="Requirements or qualifications")
    benefits: Optional[str] = Field("", max_length=5000, description="Benefits text")
    company_profile: Optional[str] = Field("", max_length=5000, description="About the organization")
    salary_range: Optional[str] = Field("", max_length=100, description="Stated compensation")
    employment_type: Optional[str] = Field("", max_length=100)
    required_experience: Optional[str] = Field("", max_length=100)
    required_education: Optional[str] = Field("", max_length=100)
    industry: Optional[str] = Field("", max_length=100)
    function: Optional[str] = Field("", max_length=100)
    telecommuting: Optional[int] = Field(0, ge=0, le=1)
    has_company_logo: Optional[int] = Field(0, ge=0, le=1)
    has_questions: Optional[int] = Field(0, ge=0, le=1)

    @field_validator("description")
    @classmethod
    def validate_description_content(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 20:
            raise ValueError("Job description must contain at least 20 characters of actual content.")
        return trimmed


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
    # Core Cybersecurity Threat Contract
    risk_level: RiskLevel                   # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_score: int                         # 0–100 (severity score)
    confidence: float                       # 0–100 % (statistical certainty)
    recommendation: str                     # Human-actionable guidance
    action: RecommendationAction            # Categorized recommendation enum

    # Pipeline & Compatibility Fields
    prediction: str                         # "FAKE" | "REAL"
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
    artifacts: Optional[ArtifactReport] = None
    findings: list[SecurityFinding] = Field(default_factory=list)
    threat_categories: list[ThreatCategory] = Field(default_factory=list)
    unified_findings: list[UnifiedFinding] = Field(default_factory=list)
    assessment_reasons: list[str] = Field(default_factory=list)
    # Phase 5: Threat Taxonomy & MITRE ATT&CK classification
    taxonomy: list[ThreatProfileResponse] = Field(default_factory=list)


class ExplainResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: int
    confidence: float
    prediction: str
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


# ── Real-time Text Ingestion Parser Schemas ───────────────────
class ParseJobTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw job posting text to parse")


class ParseJobTextResponse(BaseModel):
    title: str = ""
    company: str = ""
    salary_range: str = ""
    employment_type: str = ""
    required_experience: str = ""
    has_company_logo: int = 0
    has_questions: int = 0
    telecommuting: int = 0
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    company_profile: str = ""

