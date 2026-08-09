import { useMemo, useState } from "react";
import { useBilling } from "../hooks/useBilling";
import Changepasswordmodal from "./Changepasswordmodal";
import ChangeEmailModal from "./ChangeEmailModal";

function formatCurrency(amount, currency = "EUR") {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: String(currency || "EUR").toUpperCase(),
  }).format(Number(amount) || 0);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function ProfileModal({ user, onClose, onTopUp, onSessionEnded }) {
  const { billing, transactions, loading, error } = useBilling();
  const [tab, setTab] = useState("account");
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [changeEmailOpen, setChangeEmailOpen] = useState(false);

  const successfulPayments = useMemo(
    () => transactions.filter((transaction) => transaction.status === "succeeded"),
    [transactions],
  );
  const fillsPurchased = successfulPayments.reduce(
    (total, transaction) => total + (Number(transaction.form_fills_purchased) || 0),
    0,
  );
  const displayName = [user?.name, user?.surname].filter(Boolean).join(" ") || user?.username || "Account";

  return (
    <>
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal profile-modal" onClick={(event) => event.stopPropagation()}>
          <div className="modal__header">
            <div className="profile-heading">
              <div className="profile-avatar" aria-hidden="true">
                {(user?.name?.[0] || user?.email?.[0] || "?").toUpperCase()}
              </div>
              <div>
                <div className="modal__title">{displayName}</div>
                <div className="profile-heading__email">{user?.email}</div>
              </div>
            </div>
            <button className="modal__close" onClick={onClose} aria-label="Close profile">
              <CloseIcon />
            </button>
          </div>

          <div className="modal__body">
            <div className="tabs profile-tabs" role="tablist" aria-label="Profile sections">
              {[
                ["account", "Account"],
                ["payments", "Payments"],
                ["security", "Security"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  className={`tab${tab === value ? " tab--active" : ""}`}
                  onClick={() => setTab(value)}
                  role="tab"
                  aria-selected={tab === value}
                >
                  {label}
                </button>
              ))}
            </div>

            {error && (
              <div className="banner banner--error">
                <span className="banner__label">Error</span>
                <span>{error}</span>
              </div>
            )}

            {tab === "account" && (
              <div className="profile-sections">
                <section className="profile-section">
                  <h3>Personal information</h3>
                  <dl className="modal__dl">
                    <div className="modal__dl-row"><dt>First name</dt><dd>{user?.name || "—"}</dd></div>
                    <div className="modal__dl-row"><dt>Surname</dt><dd>{user?.surname || "—"}</dd></div>
                    <div className="modal__dl-row"><dt>Email</dt><dd>{user?.email || "—"}</dd></div>
                    <div className="modal__dl-row">
                      <dt>Email status</dt>
                      <dd><span className={`profile-status profile-status--${user?.email_verified ? "ok" : "warning"}`}>
                        {user?.email_verified ? "Verified" : "Not verified"}
                      </span></dd>
                    </div>
                    <div className="modal__dl-row"><dt>Member since</dt><dd>{formatDate(user?.created_at)}</dd></div>
                  </dl>
                </section>

                <section className="profile-section">
                  <div className="profile-section__header">
                    <h3>Usage</h3>
                    <button className="profile-link-btn" onClick={onTopUp}>Top up →</button>
                  </div>
                  {loading ? <div className="runs-empty">Loading…</div> : (
                    <div className="profile-metrics">
                      <div className="profile-metric"><strong>{billing?.form_fills_remaining ?? 0}</strong><span>Fills remaining</span></div>
                      <div className="profile-metric"><strong>{billing?.form_fills_used ?? 0}</strong><span>Fills used</span></div>
                      <div className="profile-metric"><strong>{fillsPurchased}</strong><span>Fills purchased</span></div>
                    </div>
                  )}
                </section>
              </div>
            )}

            {tab === "payments" && (
              <section className="profile-section">
                <div className="profile-metrics profile-metrics--payments">
                  <div className="profile-metric"><strong>{successfulPayments.length}</strong><span>Successful payments</span></div>
                  <div className="profile-metric"><strong>{formatCurrency(billing?.total_amount_paid)}</strong><span>Total paid</span></div>
                  <div className="profile-metric"><strong>{fillsPurchased}</strong><span>Fills purchased</span></div>
                </div>
                <h3>Payment audit</h3>
                {loading && <div className="runs-empty">Loading…</div>}
                {!loading && transactions.length === 0 && <div className="runs-empty">No payments yet.</div>}
                {!loading && transactions.length > 0 && (
                  <div className="profile-payment-list">
                    {transactions.map((transaction) => (
                      <div className="profile-payment" key={transaction.id}>
                        <div>
                          <strong>{transaction.description || "Form-fill top-up"}</strong>
                          <span>{formatDate(transaction.created_at)} · {transaction.status}</span>
                        </div>
                        <div className="profile-payment__amount">
                          <strong>{formatCurrency(transaction.amount, transaction.currency)}</strong>
                          <span>+{transaction.form_fills_purchased} fills</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {tab === "security" && (
              <div className="profile-sections">
                <section className="profile-section">
                  <h3>Sign-in methods</h3>
                  <div className="profile-methods">
                    {user?.has_password && <span className="trait-tag">Password</span>}
                    {user?.has_google_login && <span className="trait-tag">Google</span>}
                    {!user?.has_password && !user?.has_google_login && <span className="trait-tag">Account session</span>}
                  </div>
                </section>
                <section className="profile-security-action">
                  <div>
                    <strong>Password</strong>
                    <p>{user?.has_password ? "Update your account password regularly." : "This account does not have password sign-in enabled."}</p>
                  </div>
                  {user?.has_password && (
                    <button className="submit-btn" onClick={() => setChangePasswordOpen(true)}>Change password</button>
                  )}
                </section>
                <section className="profile-security-action">
                  <div>
                    <strong>Sign-in email</strong>
                    <p>{user?.has_password ? "Changing it requires your current password and verification of the new address." : "Email changes are unavailable for Google-only accounts."}</p>
                  </div>
                  {user?.has_password && (
                    <button className="submit-btn" onClick={() => setChangeEmailOpen(true)}>Change email</button>
                  )}
                </section>
              </div>
            )}
          </div>
        </div>
      </div>

      {changePasswordOpen && (
        <Changepasswordmodal
          email={user?.email}
          onClose={() => setChangePasswordOpen(false)}
          onSuccess={onSessionEnded}
        />
      )}
      {changeEmailOpen && (
        <ChangeEmailModal
          currentEmail={user?.email}
          onClose={() => setChangeEmailOpen(false)}
          onSuccess={onSessionEnded}
        />
      )}
    </>
  );
}
