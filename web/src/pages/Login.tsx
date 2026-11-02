import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthProvider";

/**
 * Email and password sign-in, with a short registration form.
 *
 * @returns The login screen, or a redirect when a session already exists.
 */
export function Login() {
  const { token, ready, signIn, register } = useAuth();
  const [mode, setMode] = useState<"sign-in" | "register">("sign-in");
  const [email, setEmail] = useState("demo.customer@example.com");
  const [password, setPassword] = useState("Demo1234!");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (ready && token) {
    return <Navigate to="/dashboard" replace />;
  }

  async function onSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await register(email, password, fullName);
      } else {
        await signIn(email, password);
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="public">
      <header className="public-bar">
        <Link className="brand" to="/">
          Harbor
        </Link>
      </header>
      <form className="auth-card" onSubmit={(event) => void onSubmit(event)}>
        <h1>{mode === "sign-in" ? "Sign in" : "Create account"}</h1>
        <p>Use your email and password. The demo customer is filled in for this proof of concept.</p>
        {mode === "register" ? (
          <label>
            Full name
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} required />
          </label>
        ) : null}
        <label>
          Email
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        {error ? <p className="banner banner-error">{error}</p> : null}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {mode === "sign-in" ? "Sign in" : "Create account"}
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => setMode(mode === "sign-in" ? "register" : "sign-in")}
        >
          {mode === "sign-in" ? "Need an account? Create one" : "Already registered? Sign in"}
        </button>
      </form>
    </div>
  );
}
