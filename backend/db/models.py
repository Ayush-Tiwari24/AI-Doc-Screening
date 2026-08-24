import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, PyEnum):
    OFFICER = "officer"
    ADMIN = "admin"
    AUDITOR = "auditor"


class DocType(str, PyEnum):
    PASSPORT = "passport"
    VISA = "visa"
    NATIONAL_ID = "national_id"
    LICENSE = "license"
    PERMIT = "permit"


class SessionStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_FACE = "awaiting_face"
    SCORED = "scored"
    COMPLETE = "complete"
    FAILED = "failed"


class RiskLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TamperingTechnique(str, PyEnum):
    ELA = "ela"
    METADATA = "metadata"
    CNN_CLASSIFIER = "cnn_classifier"


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))

    users: Mapped[list["User"]] = relationship(back_populates="checkpoint")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)
    checkpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkpoints.id", ondelete="SET NULL")
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    checkpoint: Mapped["Checkpoint | None"] = relationship(back_populates="users")


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    traveler_ref_id: Mapped[str | None] = mapped_column(String(100))
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    checkpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkpoints.id", ondelete="SET NULL")
    )
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status"), default=SessionStatus.PENDING, nullable=False
    )
    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[RiskLevel | None] = mapped_column(SAEnum(RiskLevel, name="risk_level"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["Document"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    face_verifications: Mapped[list["FaceVerification"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="session")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[DocType] = mapped_column(SAEnum(DocType, name="doc_type"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ScreeningSession"] = relationship(back_populates="documents")
    extracted_data: Mapped["ExtractedData | None"] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    tampering_results: Mapped[list["TamperingResult"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    doc_number: Mapped[str | None] = mapped_column(String(100))
    nationality: Mapped[str | None] = mapped_column(String(100))
    dob: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    doe: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gender: Mapped[str | None] = mapped_column(String(20))
    mrz_raw: Mapped[str | None] = mapped_column(Text)
    extra_fields: Mapped[dict | None] = mapped_column(JSONB)
    ocr_confidence: Mapped[float | None] = mapped_column(Float)

    document: Mapped["Document"] = relationship(back_populates="extracted_data")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details: Mapped[str | None] = mapped_column(Text)

    document: Mapped["Document"] = relationship(back_populates="validation_results")


class TamperingResult(Base):
    __tablename__ = "tampering_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    technique: Mapped[TamperingTechnique] = mapped_column(
        SAEnum(TamperingTechnique, name="tampering_technique"), nullable=False
    )
    suspicious_score: Mapped[float | None] = mapped_column(Float)
    heatmap_path: Mapped[str | None] = mapped_column(String(500))
    details: Mapped[dict | None] = mapped_column(JSONB)

    document: Mapped["Document"] = relationship(back_populates="tampering_results")


class FaceVerification(Base):
    __tablename__ = "face_verification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False
    )
    doc_photo_path: Mapped[str | None] = mapped_column(String(500))
    live_photo_path: Mapped[str | None] = mapped_column(String(500))
    similarity_score: Mapped[float | None] = mapped_column(Float)
    match: Mapped[bool | None] = mapped_column(Boolean)

    session: Mapped["ScreeningSession"] = relationship(back_populates="face_verifications")


class BlacklistEntry(Base):
    __tablename__ = "blacklist_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_number: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str | None] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(Text)
    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screening_sessions.id", ondelete="RESTRICT")
    )
    officer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    session: Mapped["ScreeningSession | None"] = relationship(back_populates="audit_logs")