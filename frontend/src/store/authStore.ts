import { create } from 'zustand';
import api, { setTokens, clearTokens, hasStoredTokens } from '../lib/api';

export interface User {
  id: string;
  name: string;
  badge_id: string;
  role: 'officer' | 'admin' | 'auditor';
  checkpoint_id: string | null;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  login: (badgeId: string, password: string) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  // Start as loading only if we have stored tokens (so protected routes
  // don't flash to login on page refresh)
  isLoading: hasStoredTokens(),

  login: async (badgeId: string, password: string) => {
    const response = await api.post('/auth/login', { badge_id: badgeId, password });
    setTokens(response.data.access_token, response.data.refresh_token);
    const meResponse = await api.get('/auth/me');
    set({ user: meResponse.data, isLoading: false });
  },

  logout: () => {
    clearTokens();
    set({ user: null, isLoading: false });
  },

  fetchCurrentUser: async () => {
    // If no tokens stored, skip fetching and immediately mark as not loading
    if (!hasStoredTokens()) {
      set({ user: null, isLoading: false });
      return;
    }
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, isLoading: false });
    } catch {
      clearTokens();
      set({ user: null, isLoading: false });
    }
  },
}));
