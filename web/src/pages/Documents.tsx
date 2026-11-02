import { useEffect, useState } from "react";
import { ApiError, apiRequest, downloadDocument } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import type { Policy, PolicyDocument } from "../types";

/**
 * Expandable document lists, one section per policy.
 *
 * @returns The My Documents page.
 */
export function Documents() {
  const { token } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Record<string, PolicyDocument[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiRequest<{ policies: Policy[] }>("/api/policies", {}, token)
      .then((payload) => {
        setPolicies(payload.policies);
        setOpen(payload.policies[0]?.policy_number ?? null);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Policies could not be loaded.");
      });
  }, [token]);

  useEffect(() => {
    if (!token || !open || documents[open]) {
      return;
    }
    apiRequest<{ documents: PolicyDocument[] }>(`/api/policies/${open}/documents`, {}, token)
      .then((payload) => {
        setDocuments((current) => ({ ...current, [open]: payload.documents }));
      })
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Documents could not be loaded.");
      });
  }, [token, open, documents]);

  async function download(document: PolicyDocument): Promise<void> {
    if (!token) {
      return;
    }
    try {
      await downloadDocument(document.document_id, document.file_name, token);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The download failed.");
    }
  }

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Documents</p>
        <h1>My Documents</h1>
        <p>Open a policy to download its documents.</p>
      </header>
      {error ? <p className="banner banner-error">{error}</p> : null}
      <div className="stack">
        {policies.map((policy) => {
          const expanded = open === policy.policy_number;
          const rows = documents[policy.policy_number] ?? [];
          return (
            <section key={policy.policy_number} className="card">
              <button type="button" className="accordion" onClick={() => setOpen(expanded ? null : policy.policy_number)}>
                <span>
                  {policy.policy_number} · {policy.product_name}
                </span>
                <span>{expanded ? "Hide" : "Show"}</span>
              </button>
              {expanded ? (
                <ul className="doc-list">
                  {rows.map((document) => (
                    <li key={document.document_id}>
                      <span>{document.title}</span>
                      <button type="button" className="btn btn-secondary" onClick={() => void download(document)}>
                        Download
                      </button>
                    </li>
                  ))}
                  {rows.length === 0 ? <li>No documents for this policy.</li> : null}
                </ul>
              ) : null}
            </section>
          );
        })}
      </div>
    </section>
  );
}
