/** Clinical Flight Deck session boundary: one authenticated role workspace per browser tab. */
import { api, type Role, type SessionUser } from "@/services/api";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type SessionValue = {
  user: SessionUser | null;
  accessToken: string | null;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<SessionUser>;
  register: (payload: { name: string; email: string; password: string; phone?: string }) => Promise<SessionUser>;
  signOut: () => void;
  demoSession: (role: Role) => void;
};

const SessionContext = createContext<SessionValue | null>(null);
const STORAGE_KEY = "opd-smartqueue-session";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // localStorage is shared by every tab on the same origin. Using it caused
    // a Doctor sign-in to overwrite an open Patient workspace. sessionStorage
    // is scoped to one tab, so concurrent role workflows remain independent.
    window.localStorage.removeItem(STORAGE_KEY);
    const serialized = window.sessionStorage.getItem(STORAGE_KEY);
    if (!serialized) return setReady(true);
    try {
      const saved = JSON.parse(serialized) as { user: SessionUser; accessToken: string };
      setUser(saved.user);
      setAccessToken(saved.accessToken);
    } finally { setReady(true); }
  }, []);

  const persist = useCallback((nextUser: SessionUser, nextToken: string) => {
    setUser(nextUser); setAccessToken(nextToken); window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ user: nextUser, accessToken: nextToken }));
  }, []);
  const signIn = useCallback(async (email: string, password: string) => { const session = await api.login(email, password); persist(session.user, session.access_token); return session.user; }, [persist]);
  const register = useCallback(async (payload: { name: string; email: string; password: string; phone?: string }) => { const session = await api.register(payload); persist(session.user, session.access_token); return session.user; }, [persist]);
  const signOut = useCallback(() => { setUser(null); setAccessToken(null); window.sessionStorage.removeItem(STORAGE_KEY); }, []);
  const demoSession = useCallback((role: Role) => { window.location.assign(`/sign-in/${role}`); }, []);
  const value = useMemo(() => ({ user, accessToken, ready, signIn, register, signOut, demoSession }), [user, accessToken, ready, signIn, register, signOut, demoSession]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() { const context = useContext(SessionContext); if (!context) throw new Error("useSession must be used within SessionProvider"); return context; }
