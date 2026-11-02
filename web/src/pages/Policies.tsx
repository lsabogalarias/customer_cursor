import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { PolicyCard } from "../components/PolicyCard";
import type { Policy } from "../types";

interface PolicyListProps {
  welcome: boolean;
}

/**
 * Shared policy list used by the dashboard and My Policies.
 *
 * @param props.welcome - When true, show the greeting.
 * @returns The policy list.
 */
export function PolicyList({ welcome }: PolicyListProps) {
  const { token, profile } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    setLoaded(false);
    apiRequest<{ policies: Policy[] }>("/api/policies", {}, token)
      .then((payload) => setPolicies(payload.policies))
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Policies could not be loaded.");
      })
      .finally(() => setLoaded(true));
  }, [token]);

  function replace(updated: Policy): void {
    setPolicies((current) =>
      current.map((item) => (item.policy_number === updated.policy_number ? updated : item)),
    );
  }

  return (
    <section>
      {welcome ? (
        <header className="page-head">
          <p className="eyebrow">Dashboard</p>
          <h1>{profile ? `Welcome, ${profile.full_name}` : "Welcome"}</h1>
          <p>These are the policies associated with your account.</p>
        </header>
      ) : (
        <header className="page-head">
          <p className="eyebrow">Policies</p>
          <h1>My Policies</h1>
        </header>
      )}
      {error ? <p className="banner banner-error">{error}</p> : null}
      {loaded && policies.length === 0 && !error ? (
        <p>No policies are associated with this account yet.</p>
      ) : null}
      <div className="card-grid">
        {token
          ? policies.map((policy) => (
              <PolicyCard key={policy.policy_number} policy={policy} token={token} onChanged={replace} />
            ))
          : null}
      </div>
    </section>
  );
}

/**
 * Dashboard with the welcome line and policy cards.
 *
 * @returns The dashboard page.
 */
export function Dashboard() {
  return <PolicyList welcome />;
}

/**
 * Policy list without the welcome section.
 *
 * @returns The My Policies page.
 */
export function Policies() {
  return <PolicyList welcome={false} />;
}
