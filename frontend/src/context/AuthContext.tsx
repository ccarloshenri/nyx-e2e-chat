import { createContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { authService } from "../services/auth/authService";
import type { AuthContextValue, LoginCredentials, RegisterCredentials, UserSession } from "../types/auth";

const TOKEN_STORAGE_KEY = "nyx.auth.token";
const USER_STORAGE_KEY = "nyx.auth.user";

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [session, setSession] = useState<UserSession | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = window.localStorage.getItem(USER_STORAGE_KEY);

    if (storedToken && storedUser) {
      try {
        const user = JSON.parse(storedUser) as UserSession["user"];
        setSession({ token: storedToken, user });
      } catch {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        window.localStorage.removeItem(USER_STORAGE_KEY);
      }
    }

    setIsRestoring(false);
  }, []);

  async function login(credentials: LoginCredentials) {
    const nextSession = await authService.login(credentials);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, nextSession.token);
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextSession.user));
    setSession(nextSession);
  }

  async function register(credentials: RegisterCredentials) {
    await authService.register(credentials);
    await login({
      username: credentials.username,
      masterPassword: credentials.masterPassword,
    });
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    window.localStorage.removeItem(USER_STORAGE_KEY);
    setSession(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      token: session?.token ?? null,
      user: session?.user ?? null,
      isAuthenticated: Boolean(session?.token),
      isRestoring,
      login,
      register,
      logout
    }),
    [session, isRestoring]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
