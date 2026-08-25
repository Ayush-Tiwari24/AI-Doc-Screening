from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_router
from api.documents import router as documents_router
from api.extraction import router as extraction_router
from api.validation import router as validation_router
from api.tampering import router as tampering_router
from api.face_verification import router as face_verification_router
from api.risk import router as risk_router
from api.websocket import router as websocket_router


app = FastAPI(
    title="AI Document Screening System"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(extraction_router)
app.include_router(validation_router)
app.include_router(tampering_router)
app.include_router(face_verification_router)
app.include_router(risk_router)
app.include_router(websocket_router)


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }