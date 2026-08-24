from fastapi import FastAPI

from auth.router import router as auth_router
from api.documents import router as documents_router
from api.extraction import router as extraction_router
from api.validation import router as validation_router
from api.tampering import router as tampering_router


app = FastAPI(
    title="AI Document Screening System"
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(extraction_router)
app.include_router(validation_router)
app.include_router(tampering_router)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }