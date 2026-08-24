import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from db.models import DocType, RiskLevel, SessionStatus


class SessionCreate(BaseModel):
    traveler_ref_id: str | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    traveler_ref_id: str | None
    officer_id: uuid.UUID
    checkpoint_id: uuid.UUID | None
    status: SessionStatus
    risk_score: float | None
    risk_level: RiskLevel | None
    created_at: datetime
    completed_at: datetime | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    doc_type: DocType
    file_path: str
    uploaded_at: datetime


class DocumentWithUrl(DocumentOut):
    view_url: str

class ExtractedDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    full_name: str | None
    doc_number: str | None
    nationality: str | None
    dob: datetime | None
    doe: datetime | None
    gender: str | None
    mrz_raw: str | None
    extra_fields: dict | None
    ocr_confidence: float | None

class ValidationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    rule_name: str
    passed: bool
    severity: str
    details: str | None

class TamperingResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    technique: str
    suspicious_score: float | None
    heatmap_path: str | None
    details: dict | None

class FaceVerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    doc_photo_path: str | None
    live_photo_path: str | None
    similarity_score: float | None
    match: bool | None
    liveness_passed: bool | None = None
    liveness_score: float | None = None

class RiskBreakdownItem(BaseModel):
    factor: str
    points: float
    raw_score: float | None = None


class RiskReportOut(BaseModel):
    session_id: uuid.UUID
    risk_score: float
    risk_level: str
    breakdown: list[RiskBreakdownItem]
    hard_override: bool