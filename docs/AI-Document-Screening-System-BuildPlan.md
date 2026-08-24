# AI-Based Fake Identity & Document Screening System
## Full Build Plan for SIH 2026 (with Claude Code prompts)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Vite)                     │
│   Officer Dashboard | Upload/Scan UI | Risk Report | Analytics    │
└───────────────────────────┬────────────────────────────────────┘
                             │ REST / WebSocket
┌───────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI - Python)                    │
│  ┌───────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │  Auth &   │ │  Document │ │   Risk       │ │  Case/Audit   │  │
│  │  RBAC     │ │  Pipeline │ │   Scoring    │ │  Trail API    │  │
│  │  Service  │ │  Orchestr.│ │   Engine     │ │               │  │
│  └───────────┘ └─────┬─────┘ └──────────────┘ └──────────────┘  │
└───────────────────────┼──────────────────────────────────────────┘
                         │
        ┌────────────────┼─────────────────┬───────────────────┐
        ▼                ▼                 ▼                   ▼
┌───────────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────────────┐
│ MODULE 1       │ │ MODULE 2     │ │ MODULE 3      │ │ MODULE 4          │
│ OCR Extraction │ │ Doc          │ │ Tampering     │ │ Face Verification │
│ (PaddleOCR /   │ │ Validation   │ │ Detection     │ │ (InsightFace /    │
│  Tesseract +   │ │ (rule engine │ │ (CNN/ELA/     │ │  DeepFace)        │
│  layout model) │ │  + regex +   │ │  metadata     │ │                   │
│                │ │  MRZ parser) │ │  forensics)   │ │                   │
└───────────────┘ └──────────────┘ └───────────────┘ └──────────────────┘
        │                │                 │                   │
        └────────────────┴─────────────────┴───────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   PostgreSQL      │
                    │  + S3/MinIO for   │
                    │  document images  │
                    │  + Redis (queue/  │
                    │  cache)           │
                    └───────────────────┘
```

**Processing flow per document:**
1. Officer uploads/scans document → stored in object storage
2. Async job queue (Celery/RQ + Redis) triggers pipeline
3. OCR → Validation → Tampering Detection → Face Verification run (some in parallel)
4. Risk Scoring Engine aggregates all module outputs into a single score + flags
5. Result + audit trail written to PostgreSQL
6. Dashboard shows result in real time via WebSocket/polling

---

## 2. Recommended Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite, TailwindCSS, shadcn/ui | Fast to build, clean dashboards, good for demo |
| Backend | Python + FastAPI | Async, great ML ecosystem, auto-generated API docs (huge for SIH judging) |
| Task Queue | Celery + Redis (or RQ for simplicity) | Document pipeline is slow — must be async |
| Database | PostgreSQL | Structured records, relations, audit logs |
| File Storage | MinIO (self-hosted S3) or AWS S3 | Store document images/scans |
| OCR | PaddleOCR (best multilingual accuracy) or Tesseract (simpler) | Passport/visa text + MRZ extraction |
| MRZ Parsing | `pymrz` / custom MRZ checksum validator | Passports/visas have machine-readable zones — huge validation win |
| Tampering Detection | Error Level Analysis (ELA) + CNN classifier (ResNet/EfficientNet fine-tuned) + PIL/EXIF metadata check | Detects photo splicing, recompression artifacts |
| Face Verification | InsightFace (ArcFace) or DeepFace | Compares document photo vs. live capture |
| Auth | JWT + role-based access (Officer / Admin / Auditor) | Needed for realistic border-security demo |
| Deployment | Docker Compose (all services) | Easy to demo, judges can run locally |

---

## 3. Database Schema (PostgreSQL)

Core tables:

```sql
-- Users (border officers, admins)
users (id, name, badge_id, role, checkpoint_id, password_hash, created_at)

-- Checkpoints
checkpoints (id, name, location, country)

-- Document scan sessions (one per traveler screening event)
screening_sessions (
  id, traveler_ref_id, officer_id, checkpoint_id,
  status, risk_score, risk_level, created_at, completed_at
)

-- Uploaded documents linked to a session
documents (
  id, session_id, doc_type ENUM(passport,visa,national_id,license,permit),
  file_path, uploaded_at
)

-- OCR extracted fields (flexible JSON + key structured fields)
extracted_data (
  id, document_id, full_name, doc_number, nationality,
  dob, doe, gender, mrz_raw, extra_fields JSONB, ocr_confidence
)

-- Validation results
validation_results (
  id, document_id, rule_name, passed BOOLEAN, details TEXT
)

-- Tampering detection results
tampering_results (
  id, document_id, technique ENUM(ela, metadata, cnn_classifier),
  suspicious_score FLOAT, heatmap_path, details JSONB
)

-- Face verification results
face_verification (
  id, session_id, doc_photo_path, live_photo_path,
  similarity_score FLOAT, match BOOLEAN
)

-- Watchlist / blacklist
blacklist_entries (id, doc_number, name, reason, added_by, added_at)

-- Audit trail (every action, immutable)
audit_logs (id, session_id, officer_id, action, timestamp, metadata JSONB)
```

---

## 4. Module-by-Module Build Order

Build in this order — each module is independently testable before wiring into the pipeline:

1. **Backend skeleton + Auth + DB** (foundation)
2. **Module 1: OCR Extraction**
3. **Module 2: Document Validation**
4. **Module 3: Tampering Detection**
5. **Module 4: Face Verification**
6. **Risk Scoring Engine** (combines 2–5)
7. **Frontend Dashboard**
8. **Integration, Docker Compose, demo dataset**

---

## 5. Step-by-Step Claude Prompts

Use these with **Claude Code** (recommended — it can create the whole repo structure and run/test code) or paste into Claude.ai chat one at a time. Do them in order; each builds on the last. Feed Claude the earlier code as context, or better, let Claude Code work directly in your repo.

### Step 0 — Project scaffolding
```
Set up a monorepo for an AI-based border document screening system with this structure:

/backend  - FastAPI app (Python 3.11), with folders: api/, services/, models/,
            db/, ml/, tasks/, tests/
/frontend - React + TypeScript + Vite + TailwindCSS + shadcn/ui
/docker   - docker-compose.yml running: backend, frontend, postgres, redis, minio

Backend should use SQLAlchemy + Alembic for migrations, Pydantic v2 for schemas,
Celery + Redis for async tasks, and JWT auth (python-jose + passlib).

Set up the docker-compose.yml so all services run with one command.
Create the initial requirements.txt / package.json.
Do not write business logic yet — just a clean, running skeleton with a
health-check endpoint and a placeholder React page that calls it.
```

### Step 1 — Database models & auth
```
Using the schema below, create SQLAlchemy models and Alembic migrations for:
users, checkpoints, screening_sessions, documents, extracted_data,
validation_results, tampering_results, face_verification,
blacklist_entries, audit_logs.

[paste the schema from section 3 above]

Then implement JWT-based auth with three roles: officer, admin, auditor.
Add endpoints: POST /auth/login, POST /auth/register (admin-only),
GET /auth/me. Add role-based dependency guards for future endpoints.
Write pytest tests for auth flows.
```

### Step 2 — Module 1: OCR Extraction
```
Build an OCR extraction service in backend/ml/ocr_service.py using PaddleOCR
(fallback to Tesseract if PaddleOCR unavailable).

Requirements:
1. Accept an image (passport/visa/national ID/license/permit) and doc_type.
2. Run OCR and get raw text + bounding boxes.
3. For passports and visas, detect and parse the MRZ (machine-readable zone,
   2 or 3 line format) using checksum validation (ICAO 9303 standard) —
   extract name, document number, nationality, DOB, expiry date, gender,
   and mark whether MRZ checksums pass.
4. For documents without MRZ (national ID, license), use regex + layout
   heuristics to extract equivalent fields.
5. Return a structured JSON: fields extracted, per-field confidence score,
   and overall OCR confidence.
6. Expose POST /documents/{id}/extract that runs this and stores results
   in extracted_data table.
Include unit tests using sample passport/visa images (generate or describe
synthetic test fixtures since real documents can't be used).
```

### Step 3 — Module 2: Document Validation
```
Build a document validation engine in backend/services/validation_service.py.

It should take extracted_data for a document and run a rule pipeline:
1. MRZ checksum validation (already computed in OCR step) — flag if failed.
2. Date logic: DOB must be in the past, expiry must be after issue date,
   document must not be expired, minimum age checks where relevant.
3. Format validation: document number format matches country-specific
   pattern (maintain a small config table of regex patterns per country/
   doc type — start with 5-10 sample countries).
4. Field consistency: name/DOB on visa must match linked passport if both
   uploaded in the same session.
5. Blacklist check: query blacklist_entries for doc_number or name match
   (exact + fuzzy match using rapidfuzz).
6. Return a list of PASS/FAIL rule results with human-readable explanations,
   store in validation_results table.
Expose POST /documents/{id}/validate. Write pytest tests covering each rule
with both passing and failing cases.
```

### Step 4 — Module 3: Tampering Detection (core AI innovation)
```
Build a tampering detection service in backend/ml/tampering_service.py with
three techniques, each returning a suspicion score 0-1:

1. Error Level Analysis (ELA): recompress the image at a known JPEG quality,
   diff against original, highlight regions with abnormal error levels
   (indicates local edits/splicing). Return a heatmap image saved to storage.

2. Metadata forensics: extract EXIF/XMP metadata with Pillow/exifread —
   flag missing metadata, inconsistent software tags (e.g. "Photoshop"),
   mismatched creation/modification timestamps, or resolution anomalies
   vs. known scanner/camera profiles.

3. CNN tamper classifier: build a lightweight CNN (transfer learning on
   EfficientNet-B0 or ResNet18, pretrained on ImageNet) that classifies
   image patches as authentic vs. manipulated. Since we won't have a large
   labeled tampered-document dataset, use a public image-forgery dataset
   (e.g. CASIA v2) for pretraining/fine-tuning as a proxy, and document this
   limitation clearly in the code comments and README.

Combine the three into a single tampering_score (weighted average, weights
configurable) and per-technique breakdown. Store in tampering_results table
with heatmap image paths. Expose POST /documents/{id}/detect-tampering.

Also add a specific check for "Photo Replacement": detect if the face-photo
region's edge/noise pattern is statistically different from the surrounding
document background (indicates a swapped photo).
```

### Step 5 — Module 4: Face Verification
```
Build a face verification service in backend/ml/face_service.py using
InsightFace (buffalo_l model) for face detection + embedding.

Requirements:
1. Detect and crop the face from the document photo region.
2. Accept a live capture (webcam photo taken at checkpoint) of the traveler.
3. Compute face embeddings for both and cosine similarity.
4. Return similarity_score and a match=True/False decision using a
   configurable threshold (default 0.6), plus liveness sanity checks
   (basic: reject if live capture appears to be a photo-of-a-photo using
   simple texture/moire analysis — note this is a basic heuristic, not
   full liveness detection).
5. Store results in face_verification table.
Expose POST /sessions/{id}/verify-face accepting a live image upload.
Write tests with sample face image pairs (same person / different person).
```

### Step 6 — Risk Scoring Engine
```
Build a risk scoring engine in backend/services/risk_engine.py that combines
outputs from validation_results, tampering_results, and face_verification
for a screening session into a single 0-100 risk score and risk_level
(LOW / MEDIUM / HIGH / CRITICAL).

Design a transparent, explainable weighted scoring model:
- Failed critical validation rules (blacklist match, expired document,
  MRZ checksum fail) → heavy weight, can push straight to CRITICAL.
- Tampering score → medium-high weight.
- Face mismatch → high weight.
- Minor validation issues (formatting warnings) → low weight.

Make weights configurable via a JSON config file, not hardcoded, since
judges/officers may want to tune sensitivity. Return a breakdown showing
which factors contributed how much to the score, in plain language
(e.g. "MRZ checksum failed (+30)", "Face similarity low: 42% (+25)").

Expose GET /sessions/{id}/risk-report returning the full explainable report.
Update screening_sessions.risk_score/risk_level when this runs.
Write tests for several scenarios (clean document, tampered, blacklisted,
face mismatch).
```

### Step 7 — Pipeline orchestration (Celery)
```
Wire modules 1-4 and the risk engine into a single async Celery pipeline
in backend/tasks/pipeline.py:

1. On document upload, trigger a Celery chain: OCR -> validate -> tamper
   detect (can run in parallel with validate) -> (if all docs in session
   processed + live photo available) face verify -> risk score.
2. Update screening_sessions.status through stages: PENDING -> PROCESSING
   -> AWAITING_FACE -> SCORED -> COMPLETE, with error handling that marks
   FAILED and logs the reason.
3. Emit progress via WebSocket (FastAPI WebSocket endpoint) so frontend can
   show live status per session.
4. Log every stage transition to audit_logs.
Write an integration test that uploads a sample document through the whole
pipeline and asserts a final risk_score is produced.
```

### Step 8 — Frontend: Officer Dashboard
```
Build the React frontend for the border officer's screening dashboard using
TailwindCSS + shadcn/ui. Pages:

1. Login page (JWT auth).
2. New Screening page: upload passport/visa/ID (drag-drop or camera capture),
   capture live traveler photo via webcam, submit to start a session.
3. Live Processing view: WebSocket-driven progress indicator through
   OCR -> Validation -> Tampering -> Face Verification -> Risk Score stages.
4. Risk Report page: big risk score badge (color-coded LOW/MED/HIGH/CRITICAL),
   expandable breakdown of every contributing factor with plain-language
   explanations, side-by-side extracted fields vs. document image with
   OCR bounding box overlay, tampering heatmap overlay toggle, face match
   confidence with both photos shown.
5. Session history / search page for auditors (searchable by traveler,
   document number, date range, risk level).
6. Admin page: manage blacklist entries, view audit logs, tune risk
   scoring weights.

Design should feel like a professional security/ops tool — dense
information, clear color coding, not consumer-app styled. Use Tailwind
design tokens for a dark, high-contrast "control room" aesthetic.
```

### Step 9 — Demo data & Docker packaging
```
Create a seed script (backend/scripts/seed_demo_data.py) that populates the
database with:
- 3 demo checkpoints and 5 demo officer accounts
- 10-15 synthetic sample "screening sessions" with a mix of clean, tampered,
  expired, and blacklisted document outcomes, using publicly available
  sample/specimen passport images (e.g. ICAO specimen documents) — never
  real personal documents.
- Pre-computed risk reports for these so the dashboard has data to show
  immediately during the SIH demo without needing live processing.

Finalize docker-compose.yml so `docker compose up` starts postgres, redis,
minio, backend (with Celery worker), and frontend, runs migrations and the
seed script automatically, and the whole system is demo-ready in under
2 minutes.
Write a README with setup instructions and an architecture diagram.
```

---

## 6. Tips Specific to SIH Judging

- **Explainability wins points.** Judges will ask "why did this get flagged?" — the risk breakdown in Step 6 is your answer. Don't skip it.
- **Use only synthetic/specimen documents** for your demo — ICAO publishes sample specimen passports for testing MRZ readers; never use real personal documents, and say this explicitly in your presentation (data privacy is a judging criterion).
- **Show a false-positive-aware story**: have one demo case where a document is flagged but a human officer overrides it — shows you understand this is decision *support*, not decision *replacement*. This maturity point scores well.
- **Have a fallback for network-free demo**: since border checkpoints may have limited connectivity, mention on-prem/edge deployment as a scalability note (all your models above run locally — that's already true, mention it).
- **Metrics to prepare**: OCR field accuracy %, tampering detection precision/recall on your test set, face-match accuracy, and average processing time per document (this directly answers "reduce verification time from minutes to seconds").

---

## 7. Suggested Team Split (if team-based)

| Person | Owns |
|---|---|
| 1 | Backend skeleton, Auth, DB, Risk Engine |
| 2 | OCR + Validation (Modules 1-2) |
| 3 | Tampering Detection (Module 3) |
| 4 | Face Verification (Module 4) + Celery pipeline |
| 5 | Frontend dashboard + demo data + presentation |

