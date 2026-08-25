// API Type Definitions — mirrors backend schemas exactly

export type DocType = 'passport' | 'visa' | 'national_id' | 'license' | 'permit';
export type SessionStatus = 'pending' | 'processing' | 'awaiting_face' | 'scored' | 'complete' | 'failed';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type UserRole = 'officer' | 'admin' | 'auditor';

// ─── Auth ────────────────────────────────────────────────────
export interface LoginRequest {
  badge_id: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  name: string;
  badge_id: string;
  role: UserRole;
  checkpoint_id: string | null;
}

// ─── Sessions ────────────────────────────────────────────────
export interface SessionCreate {
  traveler_ref_id?: string | null;
}

export interface SessionOut {
  id: string;
  traveler_ref_id: string | null;
  officer_id: string;
  checkpoint_id: string | null;
  status: SessionStatus;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  created_at: string;
  completed_at: string | null;
}

// ─── Documents ───────────────────────────────────────────────
export interface DocumentOut {
  id: string;
  session_id: string;
  doc_type: DocType;
  file_path: string;
  uploaded_at: string;
}

export interface DocumentWithUrl extends DocumentOut {
  view_url: string;
}

// ─── Extraction ──────────────────────────────────────────────
export interface ExtractedDataOut {
  id: string;
  document_id: string;
  full_name: string | null;
  doc_number: string | null;
  nationality: string | null;
  dob: string | null;
  doe: string | null;
  gender: string | null;
  mrz_raw: string | null;
  extra_fields: Record<string, unknown> | null;
  ocr_confidence: number | null;
}

// ─── Validation ──────────────────────────────────────────────
export interface ValidationResultOut {
  id: string;
  document_id: string;
  rule_name: string;
  passed: boolean;
  severity: 'info' | 'warning' | 'critical';
  details: string | null;
}

// ─── Tampering ───────────────────────────────────────────────
export interface TamperingResultOut {
  id: string;
  document_id: string;
  technique: 'ela' | 'metadata' | 'cnn_classifier' | 'photo_swap';
  suspicious_score: number | null;
  heatmap_path: string | null;
  details: Record<string, unknown> | null;
}

// ─── Face Verification ───────────────────────────────────────
export interface FaceVerificationOut {
  id: string;
  session_id: string;
  doc_photo_path: string | null;
  live_photo_path: string | null;
  similarity_score: number | null;
  match: boolean | null;
  liveness_passed: boolean | null;
  liveness_score: number | null;
}

// ─── Risk ─────────────────────────────────────────────────────
export interface RiskBreakdownItem {
  factor: string;
  points: number;
  raw_score: number | null;
}

export interface RiskReportOut {
  session_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  breakdown: RiskBreakdownItem[];
  hard_override: boolean;
}

// ─── WebSocket Events ─────────────────────────────────────────
export interface WsConnectedEvent {
  type: 'connected';
  session_id: string;
}

export interface WsStatusEvent {
  type: 'status_update';
  session_id: string;
  status: SessionStatus;
  message?: string;
}

export interface WsErrorEvent {
  type: 'error';
  session_id: string;
  message: string;
}

export type WsEvent = WsConnectedEvent | WsStatusEvent | WsErrorEvent | Record<string, unknown>;

// ─── Health ──────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
}

// ─── Demo Data Types ─────────────────────────────────────────
export interface DigiLockerField {
  label: string;
  extracted: string;
  reference: string;
  match: boolean;
}

export interface DigiLockerRecord {
  source: string;
  mode: 'demo';
  status: 'matched' | 'mismatched' | 'unavailable';
  fields: DigiLockerField[];
}
