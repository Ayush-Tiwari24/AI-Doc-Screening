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


## Infrastructure (Postgres, Redis, MinIO)

Start the dev infra containers:
```bash
cd docker
docker compose -f docker-compose.dev.yml up -d
```

Verify all connections:
```bash
cd backend
python scripts\test_connections.py
```

Services:
- Postgres: localhost:5432 (user: docuser, db: docscreening)
- Redis: localhost:6379
- MinIO: localhost:9000 (console: localhost:9001, login: minioadmin/minioadmin)

Stop the infra:
```bash
docker compose -f docker-compose.dev.yml down
```