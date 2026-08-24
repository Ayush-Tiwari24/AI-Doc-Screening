import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import DocumentOut, DocumentWithUrl, SessionCreate, SessionOut
from auth.dependencies import get_current_user
from db.models import Document, DocType, ScreeningSession, User
from db.session import get_session
from storage.client import get_presigned_url, upload_file

router = APIRouter(tags=["sessions"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    new_session = ScreeningSession(
        traveler_ref_id=payload.traveler_ref_id,
        officer_id=current_user.id,
        checkpoint_id=current_user.checkpoint_id,
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    return new_session


@router.post(
    "/sessions/{session_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    session_id: uuid.UUID,
    doc_type: DocType,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(ScreeningSession).where(ScreeningSession.id == session_id)
    )
    screening_session = result.scalar_one_or_none()
    if screening_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: jpg, png, pdf",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB",
        )

    extension = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    object_name = f"sessions/{session_id}/{doc_type.value}_{uuid.uuid4().hex}.{extension}"

    # Write to a temp file since upload_file() expects a filesystem path
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        upload_file(tmp_path, object_name)
    finally:
        os.unlink(tmp_path)

    document = Document(session_id=session_id, doc_type=doc_type, file_path=object_name)
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentWithUrl])
async def list_documents(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Document).where(Document.session_id == session_id))
    documents = result.scalars().all()

    return [
        DocumentWithUrl(
            id=doc.id,
            session_id=doc.session_id,
            doc_type=doc.doc_type,
            file_path=doc.file_path,
            uploaded_at=doc.uploaded_at,
            view_url=get_presigned_url(doc.file_path),
        )
        for doc in documents
    ]