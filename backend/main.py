from fastapi import FastAPI

from auth.router import router as auth_router

app = FastAPI(title="AI Document Screening System")

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}