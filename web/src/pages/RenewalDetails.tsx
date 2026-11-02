import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, apiRequest } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import type { Policy, RenewalQuote } from "../types";
import { formatMoney, formatStatus } from "../types";

/**
 * Renewal figures and the renew action.
 *
 * @returns The renewal details page.
 */
export function RenewalDetails() {
  const { policyNumber = "" } = useParams();
  const { token } = useAuth();
  const [quote, setQuote] = useState<RenewalQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiRequest<RenewalQuote>(`/api/policies/${policyNumber}/renewal`, {}, token)
      .then(setQuote)
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Renewal details could not be loaded.");
      });
  }, [token, policyNumber]);

  async function renew(): Promise<void> {
    if (!token) {
      return;
    }
    try {
      const updated = await apiRequest<Policy>(`/api/policies/${policyNumber}/renew`, { method: "POST" }, token);
      setQuote((current) => (current ? { ...current, status: updated.status } : current));
      setNotice("Renewal requested.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Renewal could not be requested.");
    }
  }

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Renewal</p>
        <h1>{policyNumber}</h1>
        <Link to={`/policies/${policyNumber}`}>Back to manage</Link>
      </header>
      {notice ? <p className="banner banner-ok">{notice}</p> : null}
      {error ? <p className="banner banner-error">{error}</p> : null}
      {quote ? (
        <article className="card">
          <dl className="facts">
            <div>
              <dt>Current premium</dt>
              <dd>{formatMoney(quote.current_premium)}</dd>
            </div>
            <div>
              <dt>Renewal premium</dt>
              <dd>{formatMoney(quote.renewal_premium)}</dd>
            </div>
            <div>
              <dt>Renewal starts</dt>
              <dd>{quote.renewal_effective_date}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{formatStatus(quote.status)}</dd>
            </div>
          </dl>
          <p>The offered premium is a local illustration. It is not a carrier rating.</p>
          <button type="button" className="btn btn-primary" onClick={() => void renew()}>
            Renew Now
          </button>
        </article>
      ) : null}
    </section>
  );
}
