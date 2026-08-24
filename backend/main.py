from fastapi import FastAPI

app = FastAPI(title="AI Document Screening System")


@app.get("/health")
def health():
    return {"status": "ok"}