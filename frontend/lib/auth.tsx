"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, clearTokens, getAccess, getRefresh, setTokens } from "./api";
import type { User } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getAccess()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.get<User>("/users/me"));
    } catch {
      setUser(null);
      clearTokens();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.post<{ access_token: string; refresh_token: string }>(
        "/auth/login",
        { email, password },
      );
      setTokens(tokens.access_token, tokens.refresh_token);
      await refresh();
    },
    [refresh],
  );

  const logout = useCallback(async () => {
    const refresh = getRefresh();
    if (refresh) {
      try {
        await api.post("/auth/logout", { refresh_token: refresh });
      } catch {
        /* локальный выход в любом случае */
      }
    }
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
