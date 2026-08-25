import { create } from 'zustand';
import api, { setTokens, clearTokens } from '../lib/api';

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
  isLoading: true,

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
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
}));
