/**
 * Centralized Demo Data — SentinelID
 *
 * All demo data is used ONLY for frontend-only features
 * that do not have real backend APIs.
 * 
 * Demo content must NEVER be presented as live government data.
 * All identities are synthetic.
 */

import type { DigiLockerRecord, SessionOut, RiskLevel } from '../types/api';

// ─── DigiLocker Demo Records ──────────────────────────────────

export const DIGILOCKER_MATCH_DEMO: DigiLockerRecord = {
  source: 'DigiLocker Sandbox',
  mode: 'demo',
  status: 'matched',
  fields: [
    { label: 'Full Name', extracted: 'Rahul Sharma', reference: 'Rahul Sharma', match: true },
    { label: 'Date of Birth', extracted: '12/05/2002', reference: '12/05/2002', match: true },
    { label: 'Document Number', extracted: 'DL-••••-3492', reference: 'DL-••••-3492', match: true },
    { label: 'Document Type', extracted: 'Driving Licence', reference: 'Driving Licence', match: true },
    { label: 'Issuing State', extracted: 'Delhi', reference: 'Delhi', match: true },
  ],
};

export const DIGILOCKER_MISMATCH_DEMO: DigiLockerRecord = {
  source: 'DigiLocker Sandbox',
  mode: 'demo',
  status: 'mismatched',
  fields: [
    { label: 'Full Name', extracted: 'Arun Kumar Verma', reference: 'Arun K. Verma', match: false },
    { label: 'Date of Birth', extracted: '08/11/1995', reference: '08/11/1995', match: true },
    { label: 'Document Number', extracted: 'IND-••••-7821', reference: 'IND-••••-9012', match: false },
    { label: 'Document Type', extracted: 'Passport', reference: 'Passport', match: true },
    { label: 'Issuing Authority', extracted: 'RPO Mumbai', reference: 'RPO Delhi', match: false },
  ],
};

export const DIGILOCKER_UNAVAILABLE: DigiLockerRecord = {
  source: 'DigiLocker Sandbox',
  mode: 'demo',
  status: 'unavailable',
  fields: [],
};

// ─── Demo Screening History (fictional identities only) ────────

export interface DemoScreeningRow {
  id: string;
  travelerRef: string;
  docType: string;
  date: string;
  riskLevel: RiskLevel;
  riskScore: number;
  status: string;
  officer: string;
}

export const DEMO_SCREENING_HISTORY: DemoScreeningRow[] = [
  {
    id: 'a1b2c3d4',
    travelerRef: 'REF-8821',
    docType: 'passport',
    date: '2026-08-25T09:12:00',
    riskLevel: 'low',
    riskScore: 18,
    status: 'complete',
    officer: 'Demo Officer',
  },
  {
    id: 'e5f6g7h8',
    travelerRef: 'REF-5530',
    docType: 'national_id',
    date: '2026-08-25T08:44:00',
    riskLevel: 'critical',
    riskScore: 87,
    status: 'complete',
    officer: 'Demo Officer',
  },
  {
    id: 'i9j0k1l2',
    travelerRef: 'REF-3341',
    docType: 'visa',
    date: '2026-08-24T16:20:00',
    riskLevel: 'medium',
    riskScore: 45,
    status: 'complete',
    officer: 'Demo Officer',
  },
  {
    id: 'm3n4o5p6',
    travelerRef: 'REF-9967',
    docType: 'license',
    date: '2026-08-24T14:05:00',
    riskLevel: 'high',
    riskScore: 68,
    status: 'complete',
    officer: 'Demo Officer',
  },
  {
    id: 'q7r8s9t0',
    travelerRef: 'REF-2214',
    docType: 'passport',
    date: '2026-08-24T11:30:00',
    riskLevel: 'low',
    riskScore: 12,
    status: 'complete',
    officer: 'Demo Officer',
  },
  {
    id: 'u1v2w3x4',
    travelerRef: 'REF-6673',
    docType: 'permit',
    date: '2026-08-23T17:45:00',
    riskLevel: 'medium',
    riskScore: 38,
    status: 'complete',
    officer: 'Demo Officer',
  },
];

// ─── Demo Analytics Data ──────────────────────────────────────

export const DEMO_RISK_DISTRIBUTION = [
  { name: 'Low', value: 54, color: 'var(--risk-low)' },
  { name: 'Medium', value: 28, color: 'var(--risk-medium)' },
  { name: 'High', value: 13, color: 'var(--risk-high)' },
  { name: 'Critical', value: 5, color: 'var(--risk-critical)' },
];

export const DEMO_SCREENINGS_OVER_TIME = [
  { date: 'Aug 19', count: 23 },
  { date: 'Aug 20', count: 31 },
  { date: 'Aug 21', count: 18 },
  { date: 'Aug 22', count: 27 },
  { date: 'Aug 23', count: 35 },
  { date: 'Aug 24', count: 29 },
  { date: 'Aug 25', count: 14 },
];

export const DEMO_DOC_TYPE_DISTRIBUTION = [
  { name: 'Passport', value: 48 },
  { name: 'Visa', value: 22 },
  { name: 'National ID', value: 18 },
  { name: 'Licence', value: 8 },
  { name: 'Permit', value: 4 },
];

export const DEMO_TAMPERING_BREAKDOWN = [
  { technique: 'ELA', flagged: 12, clean: 88 },
  { technique: 'Metadata', flagged: 7, clean: 93 },
  { technique: 'CNN', flagged: 5, clean: 95 },
  { technique: 'Photo Swap', flagged: 3, clean: 97 },
];

export const DEMO_METRICS = {
  screeningsToday: '--',
  cleared: '--',
  flagged: '--',
  avgTime: '--',
  note: 'Live metrics unavailable — backend does not expose aggregate endpoint',
};

// ─── Demo Scenario Sessions ───────────────────────────────────
// Used for jury demo mode — clearly labeled as demo scenarios

export interface DemoScenario {
  id: string;
  label: string;
  description: string;
  digilockerRecord: DigiLockerRecord;
  simulatedRiskLevel: RiskLevel;
  simulatedRiskScore: number;
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'genuine',
    label: 'Genuine Document',
    description: 'A complete screening of a genuine passport — all checks pass, low risk.',
    digilockerRecord: DIGILOCKER_MATCH_DEMO,
    simulatedRiskLevel: 'low',
    simulatedRiskScore: 12,
  },
  {
    id: 'tampered',
    label: 'Tampered Document',
    description: 'ELA and CNN detect image manipulation. High risk flagged.',
    digilockerRecord: DIGILOCKER_MATCH_DEMO,
    simulatedRiskLevel: 'high',
    simulatedRiskScore: 72,
  },
  {
    id: 'face_mismatch',
    label: 'Face Mismatch',
    description: 'Document is genuine but live face does not match document photo.',
    digilockerRecord: DIGILOCKER_MATCH_DEMO,
    simulatedRiskLevel: 'critical',
    simulatedRiskScore: 91,
  },
  {
    id: 'digilocker_mismatch',
    label: 'DigiLocker Mismatch',
    description: 'Authoritative source data does not match OCR-extracted fields.',
    digilockerRecord: DIGILOCKER_MISMATCH_DEMO,
    simulatedRiskLevel: 'high',
    simulatedRiskScore: 65,
  },
];

// placeholder to satisfy type import
export type _SessionOut = SessionOut;
