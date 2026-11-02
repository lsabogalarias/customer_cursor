import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import type { Payment } from "../types";
import { formatMoney, formatStatus } from "../types";

/**
 * Payment history and the mock pay action.
 *
 * @returns The My Payments page.
 */
export function Payments() {
  const { token } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiRequest<{ payments: Payment[] }>("/api/payments", {}, token)
      .then((payload) => setPayments(payload.payments))
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Payments could not be loaded.");
      });
  }, [token]);

  async function pay(paymentId: string): Promise<void> {
    if (!token) {
      return;
    }
    setBusyId(paymentId);
    setError(null);
    try {
      const updated = await apiRequest<Payment>(`/api/payments/${paymentId}/pay`, { method: "POST" }, token);
      setPayments((current) => current.map((item) => (item.payment_id === updated.payment_id ? updated : item)));
      setNotice(`Payment received. Confirmation ${updated.confirmation_id ?? ""}.`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The payment could not be completed.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Billing</p>
        <h1>My Payments</h1>
        <p>Pending amounts are sent to a mock payment gateway. No card is charged.</p>
      </header>
      {notice ? <p className="banner banner-ok">{notice}</p> : null}
      {error ? <p className="banner banner-error">{error}</p> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Policy</th>
              <th>Description</th>
              <th>Due</th>
              <th>Amount</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr key={payment.payment_id}>
                <td>{payment.policy_number}</td>
                <td>{payment.description}</td>
                <td>{payment.due_date}</td>
                <td>{formatMoney(payment.amount)}</td>
                <td>{formatStatus(payment.status)}</td>
                <td>
                  {payment.status === "pending" ? (
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={busyId === payment.payment_id}
                      onClick={() => void pay(payment.payment_id)}
                    >
                      Pay now
                    </button>
                  ) : (
                    <span className="muted">{payment.confirmation_id}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
