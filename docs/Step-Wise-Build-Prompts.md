# Step-Wise Claude Code Prompts — Build From Zero
## AI-Based Fake Identity & Document Screening System

How to use this: open an empty folder in Claude Code (or `claude` in terminal)
and run these prompts **in order, one at a time**. Let Claude finish and run/test
each step before moving to the next — don't batch multiple steps into one prompt,
the pipeline has real dependencies (DB before API, API before frontend calls, etc).
After each step, actually run the app and sanity-check before continuing.

---

## PHASE A — Foundations

### Step 1 — Repo & environment init
```
I'm building "AI-Based Fake Identity & Document Screening System" — a border
checkpoint document screening tool. Initialize an empty monorepo from scratch:

/backend   - Python 3.11 FastAPI project
/frontend  - React 18 + TypeScript + Vite project
/docker    - docker-compose config
/docs      - architecture notes

Set up:
- Git repo with a sensible .gitignore for Python + Node
- backend: pyproject.toml (or requirements.txt), virtual env instructions,
  black + ruff for linting, pytest for testing
- frontend: Vite + React + TS template, ESLint + Prettier configured
- A root README.md with project description and how to run both halves
  locally without Docker (for now — we'll containerize later)

Don't add business logic yet. Just get both halves running:
backend `uvicorn main:app --reload` returns {"status":"ok"} on GET /health,
frontend dev server shows a blank "Hello" page. Confirm both run.
```

### Step 2 — Postgres + Redis + MinIO, no Docker yet (local dev)
```
Add PostgreSQL, Redis, and MinIO (S3-compatible storage) to the backend project.

1. Add SQLAlchemy 2.0 (async) + Alembic for migrations, with connection
   settings read from a .env file (DATABASE_URL, REDIS_URL, MINIO_* vars).
2. Add a db/session.py with async engine + session factory.
3. Add a storage/client.py wrapping boto3 (S3-compatible) for MinIO,
   with upload_file() / get_presigned_url() helpers.
4. Add config.py using pydantic-settings to load all env vars in one place.
5. Write a docker/docker-compose.dev.yml that ONLY runs postgres, redis,
   and minio (not the app itself) — so I can develop the app locally
   against containerized infra. Include a minio bucket auto-create step.
6. Update README with `docker compose -f docker/docker-compose.dev.yml up`
   instructions and how to point the backend .env at them.

Verify by writing a tiny script that connects to all three and prints success.
```

### Step 3 — Database schema & migrations
```
Using this schema, create SQLAlchemy models (backend/db/models.py) and
generate the initial Alembic migration:

[paste the full schema: users, checkpoints, screening_sessions, documents,
extracted_data, validation_results, tampering_results, face_verification,
blacklist_entries, audit_logs]

Use proper types: UUID primary keys, enums for status/doc_type/risk_level,
JSONB for flexible fields, timestamps with timezone, and foreign keys with
appropriate ON DELETE behavior (cascade for session->documents, restrict
for audit_logs).

Run the migration against the dev database from Step 2 and confirm all
tables exist with `\dt` in psql.
```

### Step 4 — Auth system
```
Implement JWT authentication in FastAPI:

1. User model already exists (role: officer/admin/auditor, checkpoint_id,
   password_hash).
2. Password hashing with passlib[bcrypt].
3. JWT issuing/verification with python-jose, access token (short-lived)
   + refresh token (longer-lived, stored hashed in DB or Redis).
4. Endpoints: POST /auth/register (admin-only, creates officer accounts),
   POST /auth/login, POST /auth/refresh, GET /auth/me, POST /auth/logout.
5. FastAPI dependency `get_current_user` and `require_role(role)` for
   protecting routes.
6. Pydantic schemas for request/response, with password never returned.

Write pytest tests: register, login success/failure, protected route
rejects missing/expired/invalid token, role guard rejects wrong role.
Use a test database (or transaction rollback per test) — don't touch dev data.
```

---

## PHASE B — Core AI Modules (build & test each standalone before wiring in)

### Step 5 — File upload endpoint
```
Add document upload handling:

1. POST /sessions - creates a new screening_session for the logged-in
   officer at their checkpoint, returns session id.
2. POST /sessions/{id}/documents - multipart upload, accepts doc_type
   (passport/visa/national_id/license/permit) + image file, validates
   file type/size (jpg/png/pdf, max 10MB), uploads to MinIO via the
   storage client from Step 2, creates a `documents` row with the
   returned object path.
3. GET /sessions/{id}/documents - lists uploaded docs with presigned
   view URLs.

Write tests using a small sample JPEG fixture. Confirm the file actually
lands in the MinIO bucket (check via mc client or the MinIO console).
```

### Step 6 — OCR extraction module
```
Now build Module 1 (OCR). Create backend/ml/ocr_service.py:

1. Install and use PaddleOCR (paddleocr package, en+multilingual model).
   If setup is too heavy for the environment, fall back to pytesseract
   and note the tradeoff in a comment.
2. Function extract_text(image_path) -> raw text lines + bounding boxes
   + per-line confidence.
3. Function parse_mrz(raw_lines) -> for passports/visas, detect the MRZ
   block (2 or 3 lines of consistent width, mostly A-Z0-9<), parse per
   ICAO 9303 format, run checksum digit validation, and return: name,
   passport/doc number, nationality, DOB, expiry date, gender, and a
   mrz_checksum_valid boolean per field group.
4. Function extract_non_mrz_fields(raw_lines, doc_type) -> regex/keyword
   based extraction for national ID / license / permit (no standard MRZ).
5. POST /documents/{id}/extract - runs the pipeline, stores result in
   extracted_data table, returns the structured JSON.

Create 2-3 synthetic test images (generate simple images with PIL drawing
text in MRZ format for testing) and write tests asserting correct field
extraction and checksum validation catches a deliberately corrupted
checksum.
```

### Step 7 — Document validation engine
```
Build Module 2. Create backend/services/validation_service.py:

1. Load extracted_data for a document.
2. Rule 1 - MRZ checksum: fail if parse_mrz flagged invalid checksums.
3. Rule 2 - Date logic: DOB in the past, expiry > today (not expired),
   expiry > issue date if issue date present.
4. Rule 3 - Format validation: maintain a config dict of regex patterns
   per country+doc_type (seed with 8-10 countries incl. India, US, UK,
   Schengen format) and check doc_number matches.
5. Rule 4 - Cross-document consistency: if session has both passport and
   visa, name/DOB should match (fuzzy match tolerant of minor OCR noise
   using rapidfuzz, threshold configurable).
6. Rule 5 - Blacklist check: exact + fuzzy match of doc_number/name
   against blacklist_entries table.
7. Each rule returns {rule_name, passed, severity, message}. Store all
   in validation_results. POST /documents/{id}/validate runs everything.

Write tests: one fully-passing document, one with each rule individually
failing, confirm severities and messages are correct and human-readable.
```

### Step 8 — Tampering detection: ELA + metadata (fast wins first)
```
Build the first half of Module 3. Create backend/ml/tampering_service.py:

1. error_level_analysis(image_path) -> resave the JPEG at quality=90,
   compute per-pixel absolute difference from original, amplify and
   save as a heatmap PNG to MinIO, return a suspicion score 0-1 based
   on variance/hotspot concentration in the diff.
2. metadata_forensics(image_path) -> extract EXIF via Pillow, flag:
   missing expected fields, editing-software tags (Photoshop/GIMP/etc
   in Software tag), DateTimeOriginal vs ModifyDate mismatch beyond a
   threshold, resolution/DPI inconsistent with a typical scanner range.
   Return suspicion score 0-1 + list of specific flags found.
3. POST /documents/{id}/detect-tampering/basic runs both, stores in
   tampering_results (technique='ela' and technique='metadata' rows).

Test with: (a) an untouched sample image -> low scores, (b) an image you
deliberately edit (paste a shape onto it, resave) -> ELA should flag the
edited region, (c) an image with Photoshop EXIF tag -> metadata flags it.
```

### Step 9 — Tampering detection: CNN classifier + photo-swap check
```
Build the second half of Module 3:

1. Set up a lightweight tamper classifier: EfficientNet-B0 (torchvision,
   pretrained on ImageNet) with a new classification head, fine-tuned on
   CASIA v2 (or an equivalent public image-forgery dataset) to classify
   authentic vs. spliced/copy-moved patches. Write the training script
   separately (backend/ml/training/train_tamper_classifier.py) — this
   doesn't run at request time, just produces a saved model checkpoint.
   Document clearly in comments that this is trained on a general
   image-forgery proxy dataset, not real forged government documents,
   since no such labeled dataset is available — state this limitation
   explicitly for the demo.
2. cnn_tamper_score(image_path) -> load the checkpoint, run inference,
   return suspicion score 0-1.
3. photo_swap_check(image_path, face_bbox) -> compare noise/edge
   statistics (e.g. Laplacian variance, JPEG block artifacts) of the
   face-photo region vs. the surrounding document background; flag if
   statistically inconsistent (indicates a pasted-in photo).
4. Combine ELA + metadata + CNN + photo-swap into a single weighted
   tampering_score (weights in a config file) and store the aggregate.
   Update POST /documents/{id}/detect-tampering to run all four and
   return the full breakdown.

Write tests with mocked/stubbed model inference so tests run fast without
needing GPU or the full training pipeline.
```

### Step 10 — Face verification module
```
Build Module 4. Create backend/ml/face_service.py:

1. Use insightface (buffalo_l model) for face detection + 512-d embedding.
2. detect_and_crop_face(image_path) -> bounding box + cropped face image,
   used on the document photo region.
3. compute_similarity(embedding_a, embedding_b) -> cosine similarity.
4. basic_liveness_check(image_path) -> simple heuristic (texture/moire
   pattern analysis via FFT) to flag "photo of a photo" attempts on the
   live capture; note clearly this is NOT full anti-spoofing liveness,
   just a basic sanity filter — state this limitation in the demo/report.
5. POST /sessions/{id}/verify-face - accepts a live webcam capture upload,
   runs against the document photo already on file, returns similarity
   score + match boolean (threshold configurable, default 0.6) + liveness
   flag, stores in face_verification table.

Test with a same-person pair (should match) and different-person pair
(should not match) using public sample face datasets (e.g. LFW samples)
— never real personal photos of identifiable individuals outside of
consented test fixtures.
```

---

## PHASE C — Bringing It Together

### Step 11 — Risk scoring engine
```
Build backend/services/risk_engine.py combining validation_results,
tampering_results, and face_verification for a session into one
explainable risk score.

1. Load a config JSON (backend/config/risk_weights.json) with weights per
   factor: blacklist_match, expired_document, mrz_checksum_fail,
   format_invalid, cross_doc_mismatch, tampering_score, face_mismatch,
   liveness_flag. Make weights hot-reloadable (read at request time, or
   cached with a short TTL) so an admin can tune them without redeploy.
2. compute_risk(session_id) -> iterate all factors that apply, sum
   weighted contributions, cap at 100, map to LOW(<30)/MEDIUM(30-59)/
   HIGH(60-84)/CRITICAL(85+), and produce a breakdown list like
   [{"factor": "MRZ checksum failed", "points": 30}, ...] in plain English.
3. Blacklist match or expired document should be able to force CRITICAL
   regardless of point total (hard override) — implement this explicitly.
4. GET /sessions/{id}/risk-report returns the full report and updates
   screening_sessions.risk_score/risk_level.

Write tests for: clean session (LOW), tampered document (escalates to
HIGH), blacklist hit (forces CRITICAL regardless of other factors), face
mismatch contribution.
```

### Step 12 — Celery pipeline orchestration
```
Wire everything into an async pipeline using Celery + Redis:

1. backend/tasks/pipeline.py: on document upload, enqueue a chain:
   run_ocr -> run_validation -> run_tampering (validation and tampering
   can run in parallel as a group, both must finish before scoring).
2. When all documents in a session are processed AND a live face capture
   is available, enqueue run_face_verification -> compute_risk.
3. Update screening_sessions.status through: PENDING -> PROCESSING ->
   AWAITING_FACE -> SCORED -> COMPLETE. On any task failure, set FAILED
   with an error reason and don't silently swallow exceptions.
4. Add a FastAPI WebSocket endpoint /ws/sessions/{id} that pushes status
   updates as the pipeline progresses (use Redis pub/sub to bridge Celery
   worker -> WebSocket process).
5. Log every status transition and module completion to audit_logs.

Write an integration test: upload a document, wait for pipeline completion
(poll or use a test broker in eager mode), assert final risk_score exists.
Add Celery worker startup instructions to README.
```

---

## PHASE D — Frontend

### Step 13 — Frontend scaffolding & auth pages
```
In /frontend, set up TailwindCSS + shadcn/ui on top of the existing Vite+
React+TS project. Build:

1. API client (frontend/src/lib/api.ts) using fetch/axios with JWT stored
   in memory + refresh handling, base URL from env var.
2. Auth context/provider (React context or Zustand) holding current user
   + token.
3. Login page matching the backend's /auth/login.
4. Protected route wrapper redirecting to /login if not authenticated.
5. Basic app shell: sidebar nav (New Screening, History, Admin — admin
   only), top bar with officer name/checkpoint/logout.

Style: dark, high-contrast "control room" aesthetic appropriate for a
security operations tool — not a consumer app look. Use Tailwind design
tokens consistently (define a small palette: background, surface,
border, risk-low/med/high/critical accent colors).
```

### Step 14 — New Screening flow
```
Build the New Screening page:

1. Start session button -> POST /sessions, navigate to session workspace.
2. Upload zone per document type (passport/visa/national ID/etc) —
   drag-drop or click-to-browse, with image preview thumbnail.
3. Webcam capture component for the live traveler photo (use the
   MediaDevices API), with a "retake" option.
4. "Run Screening" button triggers document uploads + face capture upload,
   then navigates to the live processing view.

Handle upload errors (wrong file type, too large) with clear inline
messages, not just console errors.
```

### Step 15 — Live processing view (WebSocket)
```
Build a processing status page that connects to /ws/sessions/{id} and
shows a step-by-step progress indicator through: Uploading -> OCR ->
Validation -> Tampering Detection -> Face Verification -> Risk Scoring
-> Complete, each step showing pending/running/done/failed state with
appropriate icons/colors. On completion, auto-navigate to the Risk
Report page. On failure, show which stage failed and why (from the
error reason in session status), with a retry option.
```

### Step 16 — Risk report page
```
Build the Risk Report page — this is the most important screen, it's
what the officer actually acts on:

1. Large color-coded risk badge (LOW green / MEDIUM yellow / HIGH orange
   / CRITICAL red) with the numeric score.
2. Expandable "Why this score" panel listing every contributing factor
   in plain language with its point contribution (from the risk_engine
   breakdown), sorted by contribution descending.
3. Document viewer: original image with OCR bounding boxes overlaid
   (toggleable), extracted fields shown side by side, each field flagged
   green/red based on its validation result.
4. Tampering panel: ELA heatmap and metadata flags shown with toggle to
   overlay on the original image, per-technique score breakdown.
5. Face verification panel: document photo + live capture side by side,
   similarity percentage, match/no-match indicator, liveness flag if any.
6. Officer decision controls: "Approve" / "Flag for secondary screening"
   / "Deny" buttons, with a required comment field, writes an audit_log
   entry — this is the human-in-the-loop override the report should show.
```

### Step 17 — History, search, and admin pages
```
Build the remaining pages:

1. History/Search page (for auditors + officers): table of past sessions,
   filterable by risk level, date range, checkpoint, searchable by
   traveler name/doc number, click-through to that session's risk report
   (read-only for completed sessions).
2. Admin page (admin role only):
   - Blacklist management: add/remove/search blacklist_entries.
   - Risk weight tuning: form editing backend/config/risk_weights.json
     values via a dedicated admin API endpoint (add this endpoint to
     the backend if not already present, admin-role protected).
   - Audit log viewer: searchable/filterable raw audit trail.
   - Officer account management: create/deactivate officer accounts.
```

---

## PHASE E — Integration & Demo Readiness

### Step 18 — Full Docker Compose
```
Consolidate everything into one production-style docker-compose.yml:
postgres, redis, minio, backend (FastAPI + Celery worker as separate
services sharing the same image), frontend (built and served, or dev
server for demo simplicity — your call, note tradeoff).

On `docker compose up`:
1. Postgres starts and is healthy before backend starts.
2. Backend runs Alembic migrations automatically on startup.
3. MinIO bucket is created if it doesn't exist.
4. Everything is reachable: frontend on :3000 (or similar), backend API
   docs on :8000/docs.

Confirm the whole stack comes up clean from `docker compose up --build`
with zero manual steps.
```

### Step 19 — Seed data for demo
```
Write backend/scripts/seed_demo_data.py:

1. Creates 3 checkpoints, 5 officer accounts (with known demo passwords),
   1 admin account.
2. Uses publicly available ICAO specimen passport images (never real
   personal documents) to create 10-15 pre-processed screening_sessions
   spanning: clean/LOW, tampered/HIGH, expired/HIGH, blacklisted/CRITICAL,
   face-mismatch/HIGH scenarios, with fully populated extracted_data,
   validation_results, tampering_results, face_verification, and risk
   scores — so the dashboard has rich, realistic data to show immediately
   without waiting on live processing during the demo.
3. Add a `make seed` / npm script / docker compose one-liner to run it.

Also add a couple of documents deliberately left in PENDING/PROCESSING
state so the live WebSocket demo has something to actually process live.
```

### Step 20 — Testing pass, README, and architecture doc
```
Do a final quality pass:

1. Run the full pytest suite and fix any failing/flaky tests.
2. Add a docs/ARCHITECTURE.md with the system diagram, data flow
   description, and explicit list of known limitations (tampering model
   trained on proxy dataset, liveness check is basic heuristic only,
   MRZ parsing covers standard ICAO formats).
3. Update root README.md with: one-command setup instructions, demo
   login credentials, a walkthrough of the 4 modules, and metrics to
   quote (OCR field accuracy, tampering detection precision/recall on
   test set, face-match accuracy, average end-to-end processing time).
4. Add a docs/DEMO_SCRIPT.md — a 3-minute walkthrough script for the
   SIH presentation: login -> new screening with a clean doc -> new
   screening with a tampered doc -> show risk report explainability ->
   show officer override -> show admin risk-weight tuning.
```

---

## Notes on sequencing

- Phases A and B can technically be parallelized across a team (each
  module in Phase B only needs Phase A's DB/auth/upload foundation).
- Don't start Phase C (Step 11) until at least Steps 6-10 are individually
  working and tested — the risk engine is only as good as its inputs.
- Frontend (Phase D) can start as soon as Phase A is done, working against
  mocked API responses, and get wired to real endpoints as Phase B/C land.
- Keep re-running Step 20's test suite after every phase, not just at the end.
