/**
 * WebSocket connection manager for screening session live status.
 * Wraps the native WebSocket with reconnect logic and event callbacks.
 */

import type { WsEvent, SessionStatus } from '../types/api';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000';

export type WsStatusCallback = (status: SessionStatus) => void;
export type WsErrorCallback = (msg: string) => void;
export type WsConnectedCallback = () => void;

interface ScreeningWsOptions {
  sessionId: string;
  onStatus: WsStatusCallback;
  onError?: WsErrorCallback;
  onConnected?: WsConnectedCallback;
  onClose?: () => void;
}

export class ScreeningWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private onStatus: WsStatusCallback;
  private onError?: WsErrorCallback;
  private onConnected?: WsConnectedCallback;
  private onClose?: () => void;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private maxReconnects = 5;
  private reconnectCount = 0;
  private closed = false;

  constructor(opts: ScreeningWsOptions) {
    this.sessionId = opts.sessionId;
    this.onStatus = opts.onStatus;
    this.onError = opts.onError;
    this.onConnected = opts.onConnected;
    this.onClose = opts.onClose;
  }

  connect() {
    if (this.closed) return;
    const url = `${WS_BASE}/ws/sessions/${this.sessionId}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.onError?.('Failed to open WebSocket connection.');
      return;
    }

    this.ws.onopen = () => {
      this.reconnectCount = 0;
      this.onConnected?.();
    };

    this.ws.onmessage = (evt) => {
      let payload: WsEvent;
      try {
        payload = JSON.parse(evt.data as string) as WsEvent;
      } catch {
        return;
      }

      const p = payload as Record<string, unknown>;

      // Handle status_update events
      if (p['type'] === 'status_update' && p['status']) {
        this.onStatus(p['status'] as SessionStatus);
        return;
      }

      // Some backends send status at top level
      if (p['status'] && typeof p['status'] === 'string') {
        this.onStatus(p['status'] as SessionStatus);
      }
    };

    this.ws.onerror = () => {
      this.onError?.('WebSocket connection error.');
    };

    this.ws.onclose = () => {
      this.onClose?.();
      if (!this.closed && this.reconnectCount < this.maxReconnects) {
        this.reconnectCount++;
        const delay = Math.min(1000 * 2 ** this.reconnectCount, 10000);
        this.reconnectTimer = setTimeout(() => this.connect(), delay);
      }
    };
  }

  disconnect() {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
