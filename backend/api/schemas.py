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