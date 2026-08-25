import { create } from 'zustand';
import type { DocType, SessionStatus, ExtractedDataOut, ValidationResultOut, TamperingResultOut, FaceVerificationOut, RiskReportOut } from '../types/api';

interface ScreeningState {
  sessionId: string | null;
  travelerRefId: string | null;
  docType: DocType | null;
  documentId: string | null;
  status: SessionStatus | null;
  extractedData: ExtractedDataOut | null;
  validationResults: ValidationResultOut[];
  tamperingResults: TamperingResultOut[];
  faceVerification: FaceVerificationOut | null;
  riskReport: RiskReportOut | null;

  setSession: (id: string, refId?: string | null) => void;
  setDocType: (type: DocType) => void;
  setDocumentId: (id: string) => void;
  setStatus: (status: SessionStatus) => void;
  setExtractedData: (data: ExtractedDataOut) => void;
  setValidationResults: (results: ValidationResultOut[]) => void;
  setTamperingResults: (results: TamperingResultOut[]) => void;
  setFaceVerification: (result: FaceVerificationOut) => void;
  setRiskReport: (report: RiskReportOut) => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  travelerRefId: null,
  docType: null,
  documentId: null,
  status: null,
  extractedData: null,
  validationResults: [],
  tamperingResults: [],
  faceVerification: null,
  riskReport: null,
};

export const useScreeningStore = create<ScreeningState>((set) => ({
  ...initialState,

  setSession: (id, refId = null) => set({ sessionId: id, travelerRefId: refId }),
  setDocType: (type) => set({ docType: type }),
  setDocumentId: (id) => set({ documentId: id }),
  setStatus: (status) => set({ status }),
  setExtractedData: (data) => set({ extractedData: data }),
  setValidationResults: (results) => set({ validationResults: results }),
  setTamperingResults: (results) => set({ tamperingResults: results }),
  setFaceVerification: (result) => set({ faceVerification: result }),
  setRiskReport: (report) => set({ riskReport: report }),
  reset: () => set(initialState),
}));
