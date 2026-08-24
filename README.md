# AI-Based Fake Identity & Document Screening System

SIH 2026 project - border checkpoint document screening with OCR, validation,
tampering detection, and face verification.

## Run locally (no Docker yet)

### Backend
```bash
cd backend
python3.11 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Health check: http://127.0.0.1:8000/health

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Status
Environment: CPU-only (no GPU) - all ML components chosen/configured accordingly.
