import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, apiRequest } from "../api/client";
import type { IdCard, Policy } from "../types";
import { formatMoney, formatStatus } from "../types";

interface PolicyCardProps {
  policy: Policy;
  token: string;
  onChanged: (policy: Policy) => void;
}

/**
 * One policy with the four portal actions.
 *
 * @param props.policy - Policy to show.
 * @param props.token - Bearer token.
 * @param props.onChanged - Called after a successful renewal request.
 * @returns A policy card.
 */
export function PolicyCard({ policy, token, onChanged }: PolicyCardProps) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [card, setCard] = useState<IdCard | null>(null);
  const [busy, setBusy] = useState(false);

  async function renew(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiRequest<Policy>(`/api/policies/${policy.policy_number}/renew`, { method: "POST" }, token);
      onChanged(updated);
      setMessage(`Renewal requested for ${updated.policy_number}.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Renewal could not be requested.");
    } finally {
      setBusy(false);
    }
  }

  async function showCard(): Promise<void> {
    setError(null);
    try {
      const next = await apiRequest<IdCard>(`/api/policies/${policy.policy_number}/id-card`, {}, token);
      setCard(next);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The ID card could not be loaded.");
    }
  }

  return (
    <article className="card">
      <header className="card-head">
        <div>
          <p className="eyebrow">{policy.product_name}</p>
          <h2>{policy.policy_number}</h2>
        </div>
        <span className={`pill pill-${policy.status}`}>{formatStatus(policy.status)}</span>
      </header>
      <dl className="facts">
        <div>
          <dt>Insured</dt>
          <dd>{policy.insured_name}</dd>
        </div>
        <div>
          <dt>Premium</dt>
          <dd>{formatMoney(policy.premium)}</dd>
        </div>
        <div>
          <dt>Term</dt>
          <dd>
            {policy.effective_date} to {policy.expiration_date}
          </dd>
        </div>
        {policy.property_address ? (
          <div>
            <dt>Property</dt>
            <dd>{policy.property_address}</dd>
          </div>
        ) : null}
      </dl>
      {message ? <p className="banner banner-ok">{message}</p> : null}
      {error ? <p className="banner banner-error">{error}</p> : null}
      <div className="actions">
        <button type="button" className="btn btn-primary" onClick={() => void renew()} disabled={busy}>
          Renew Now
        </button>
        <Link className="btn btn-secondary" to={`/policies/${policy.policy_number}/renewal`}>
          Renewal Details
        </Link>
        <button type="button" className="btn btn-secondary" onClick={() => void showCard()}>
          Id Card
        </button>
        <Link className="btn btn-secondary" to={`/policies/${policy.policy_number}`}>
          Manage
        </Link>
      </div>
      {card ? (
        <div className="modal-back" role="presentation" onClick={() => setCard(null)}>
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="id-card-title" onClick={(event) => event.stopPropagation()}>
            <h3 id="id-card-title">Insurance ID card</h3>
            <p>
              {card.insured_name} · {card.policy_number}
            </p>
            <p>
              {card.effective_date} to {card.expiration_date}
            </p>
            {card.property_address ? <p>{card.property_address}</p> : null}
            {card.vehicles.length > 0 ? (
              <ul>
                {card.vehicles.map((vehicle) => (
                  <li key={vehicle.vehicle_id}>
                    {vehicle.year} {vehicle.make} {vehicle.model} · VIN {vehicle.vin}
                  </li>
                ))}
              </ul>
            ) : null}
            <button type="button" className="btn btn-secondary" onClick={() => setCard(null)}>
              Close
            </button>
          </section>
        </div>
      ) : null}
    </article>
  );
}
