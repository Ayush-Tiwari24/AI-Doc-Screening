from fastapi import FastAPI

from auth.router import router as auth_router
from api.documents import router as documents_router

app = FastAPI(title="AI Document Screening System")

app.include_router(auth_router)
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "ok"}