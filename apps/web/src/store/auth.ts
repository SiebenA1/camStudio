"use client";

import { create } from "zustand";
import type { User } from "@/lib/types";
import { clearToken, getToken, setToken } from "@/lib/api";

interface AuthState {
  user: User | null;
  token: string | null;
  loaded: boolean;
  setAuth: (token: string, user: User) => void;
  setUser: (user: User) => void;
  logout: () => void;
  init: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: null,
  loaded: false,
  setAuth: (token, user) => {
    setToken(token);
    set({ token, user, loaded: true });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    clearToken();
    set({ token: null, user: null, loaded: true });
  },
  init: () => {
    const token = getToken();
    set({ token, loaded: true });
  },
}));
