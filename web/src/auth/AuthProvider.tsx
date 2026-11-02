import { createContext, useContext, useEffect, useState } from "react";
import { apiRequest } from "../api/client";
import type { UserProfile } from "../types";

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthState {
  token: string | null;
  profile: UserProfile | null;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

/**
 * Hold the portal session in sessionStorage and load the profile.
 *
 * @param props.children - Application tree.
 * @returns The provider element.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem("portal_token"));
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!token) {
      setProfile(null);
      setReady(true);
      return;
    }
    let cancelled = false;
    apiRequest<UserProfile>("/api/auth/me", {}, token)
      .then((next) => {
        if (!cancelled) {
          setProfile(next);
        }
      })
      .catch(() => {
        sessionStorage.removeItem("portal_token");
        if (!cancelled) {
          setToken(null);
          setProfile(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setReady(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function signIn(email: string, password: string): Promise<void> {
    const result = await apiRequest<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    sessionStorage.setItem("portal_token", result.access_token);
    setReady(false);
    setToken(result.access_token);
  }

  async function register(email: string, password: string, fullName: string): Promise<void> {
    await apiRequest<UserProfile>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    await signIn(email, password);
  }

  function signOut(): void {
    sessionStorage.removeItem("portal_token");
    setToken(null);
    setProfile(null);
    setReady(true);
  }

  return (
    <AuthContext.Provider value={{ token, profile, ready, signIn, register, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Read the current session. Must be used under AuthProvider.
 *
 * @returns The session state and actions.
 */
export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return value;
}
