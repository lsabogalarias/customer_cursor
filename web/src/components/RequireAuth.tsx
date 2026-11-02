import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

/**
 * Send anonymous visitors to the login screen.
 *
 * @returns The protected outlet, a loading line, or a redirect.
 */
export function RequireAuth() {
  const { token, ready } = useAuth();
  if (!ready) {
    return <p className="loading">Loading your session…</p>;
  }
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
