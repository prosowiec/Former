import { useState, useEffect } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import { api } from "../api/client";
import { useBilling } from "../hooks/useBilling";

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? "");

const FILLS_PER_EUR = 10;

const TIERS = [
  { label: "Starter",     eur: 5,   fills: 50,  note: "Good for testing" },
  { label: "Standard",    eur: 10,  fills: 100, note: "Most popular" },
  { label: "Pro",         eur: 25,  fills: 250, note: "Best value" },
];

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function formatCurrency(amount, currency = "eur") {
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: currency.toUpperCase(),
  }).format(amount);
}

// ── Stripe Payment Form ───────────────────────────────────
function CheckoutForm({ amountEur, fills, onSuccess, onCancel }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handlePay(e) {
    e.preventDefault();
    
    if (!stripe || !elements) {
      setError("Stripe is not loaded. Please refresh the page.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      // Step 2: Confirm payment using Elements
      const { error: confirmError, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          // Note: If using redirect-based methods (like iDEAL), specify a return_url here:
          // return_url: window.location.origin + "/billing/success",
        },
        redirect: "if_required", // Prevents page reload for cards/Apple Pay
      });

      if (confirmError) {
        console.error("Payment confirmation error:", confirmError);
        throw new Error(confirmError.message);
      }

      if (!paymentIntent) {
        throw new Error("No payment intent returned from Stripe");
      }

      console.log("Payment intent status:", paymentIntent.status);

      if (paymentIntent.status !== "succeeded") {
        throw new Error(`Payment failed with status: ${paymentIntent.status}`);
      }

      // Step 3: Confirm payment on backend
      console.log("Confirming payment on backend");
      await api.confirmPayment({
        payment_intent_id: paymentIntent.id,
        stripe_transaction_id: paymentIntent.id,
      });

      console.log("Payment successful!");
      onSuccess(fills);
    } catch (err) {
      console.error("Payment error:", err);
      setError(err.message || "Payment failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="billing-checkout" onSubmit={handlePay}>
      <div className="billing-checkout__summary">
        <span className="billing-checkout__amount">{formatCurrency(amountEur)}</span>
        <span className="billing-checkout__fills">→ {fills} form fills</span>
      </div>

      <div className="billing-card-element" style={{ marginBottom: "20px" }}>
        <PaymentElement />
      </div>

      {error && (
        <div className="banner banner--error">
          <span className="banner__label">Error</span>
          <span>{error}</span>
        </div>
      )}

      <div className="billing-checkout__actions">
        <button type="button" className="billing-btn billing-btn--ghost" onClick={onCancel}>
          Back
        </button>
        <button
          type="submit"
          className="billing-btn billing-btn--primary"
          disabled={!stripe || loading}
        >
          {loading ? <span className="spinner" /> : `Pay ${formatCurrency(amountEur)}`}
        </button>
      </div>
    </form>
  );
}

// ── Main modal ────────────────────────────────────────────
export default function BillingModal({ onClose }) {
  const { billing, transactions, loading, refetch } = useBilling();
  const [step, setStep] = useState("overview"); // overview | checkout | success
  const [selected, setSelected] = useState(null); // { eur, fills }
  const [clientSecret, setClientSecret] = useState(null); // Added for PaymentElement
  const [intentLoading, setIntentLoading] = useState(false); // Tracks backend call
  const [customEur, setCustomEur] = useState("");
  const [tab, setTab] = useState("topup"); // topup | history

  const customFills = Math.floor(Number(customEur) * FILLS_PER_EUR);
  const customValid = customEur !== "" && Number(customEur) >= 1;
  
  // Check if Stripe is configured
  const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
  const stripeConfigured = !!stripePublishableKey && stripePublishableKey !== "";

  // Step 1: Create PaymentIntent as soon as a tier is selected
  async function selectTier(tier) {
    setSelected({ eur: tier.eur, fills: tier.fills });
    setIntentLoading(true);
    try {
      const intentResponse = await api.createPaymentIntent({
        amount_eur: tier.eur,
        form_fills_purchased: tier.fills,
      });
      setClientSecret(intentResponse.client_secret);
      setStep("checkout");
    } catch (err) {
      console.error("Failed to create payment intent", err);
    } finally {
      setIntentLoading(false);
    }
  }

  async function selectCustom() {
    if (!customValid) return;
    setSelected({ eur: Number(customEur), fills: customFills });
    setIntentLoading(true);
    try {
      const intentResponse = await api.createPaymentIntent({
        amount_eur: Number(customEur),
        form_fills_purchased: customFills,
      });
      setClientSecret(intentResponse.client_secret);
      setStep("checkout");
    } catch (err) {
      console.error("Failed to create payment intent", err);
    } finally {
      setIntentLoading(false);
    }
  }

  async function handleSuccess(fills) {
    await refetch();
    setStep("success");
  }

  function handleCancel() {
    setStep("overview");
    setClientSecret(null);
  }

  // Trap focus / close on Escape
  useEffect(() => {
    function onKey(e) { if (e.key === "Escape") onClose(); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal billing-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="modal__header">
          <div className="modal__title-group">
            <span className="modal__title">Billing</span>
            {billing && (
              <span className="billing-balance">
                <span className="billing-balance__count">{billing.form_fills_remaining}</span>
                <span className="billing-balance__label">fills remaining</span>
              </span>
            )}
          </div>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        {/* Body */}
        <div className="modal__body">

          {step === "success" && (
            <div className="billing-success">
              <span className="billing-success__icon">✓</span>
              <span className="billing-success__msg">Payment recorded. Your fills have been added.</span>
              <button className="billing-btn billing-btn--primary" onClick={() => setStep("overview")}>
                Done
              </button>
            </div>
          )}

          {step === "checkout" && selected && (
            <>
              {!stripeConfigured && (
                <div className="banner banner--error">
                  <span className="banner__label">Configuration Error</span>
                  <span>Stripe is not configured. Please set STRIPE_PUBLISHABLE_KEY environment variable.</span>
                </div>
              )}
              {stripeConfigured && clientSecret && (
                <Elements stripe={stripePromise} options={{ clientSecret }}>
                  <CheckoutForm
                    amountEur={selected.eur}
                    fills={selected.fills}
                    onSuccess={handleSuccess}
                    onCancel={handleCancel}
                  />
                </Elements>
              )}
              {(!stripeConfigured || !clientSecret) && (
                <div className="billing-checkout__actions">
                  <button type="button" className="billing-btn billing-btn--ghost" onClick={handleCancel}>
                    Back
                  </button>
                </div>
              )}
            </>
          )}

          {step === "overview" && (
            <>
              {/* Tabs */}
              <div className="tabs">
                <button className={`tab${tab === "topup" ? " tab--active" : ""}`} onClick={() => setTab("topup")}>Top up</button>
                <button className={`tab${tab === "history" ? " tab--active" : ""}`} onClick={() => setTab("history")}>History</button>
              </div>

              {tab === "topup" && (
                <div className="billing-topup">
                  {/* Stats */}
                  {billing && !loading && (
                    <div className="billing-stats">
                      <div className="billing-stat">
                        <span className="billing-stat__val">{billing.form_fills_remaining}</span>
                        <span className="billing-stat__label">Remaining</span>
                      </div>
                      <div className="billing-stat">
                        <span className="billing-stat__val">{billing.form_fills_used}</span>
                        <span className="billing-stat__label">Used</span>
                      </div>
                      <div className="billing-stat">
                        <span className="billing-stat__val">{formatCurrency(billing.total_amount_paid)}</span>
                        <span className="billing-stat__label">Total paid</span>
                      </div>
                    </div>
                  )}

                  <p className="billing-rate">1 EUR = {FILLS_PER_EUR} form fills</p>

                  {/* Tiers */}
                  <div className="billing-tiers">
                    {TIERS.map((t) => (
                      <button
                        key={t.label}
                        className="billing-tier"
                        onClick={() => selectTier(t)}
                        disabled={intentLoading}
                      >
                        <div className="billing-tier__top">
                          <span className="billing-tier__label">{t.label}</span>
                          <span className="billing-tier__note">{t.note}</span>
                        </div>
                        <span className="billing-tier__price">{formatCurrency(t.eur)}</span>
                        <span className="billing-tier__fills">{t.fills} fills</span>
                      </button>
                    ))}
                  </div>

                  {/* Custom */}
                  <div className="billing-custom">
                    <div className="billing-custom__input-wrap">
                      <span className="billing-custom__currency">€</span>
                      <input
                        className="billing-custom__input"
                        type="number"
                        min="1"
                        step="1"
                        placeholder="Custom amount"
                        value={customEur}
                        onChange={(e) => setCustomEur(e.target.value)}
                        disabled={intentLoading}
                      />
                      {customEur && (
                        <span className="billing-custom__preview">
                          = {customFills} fills
                        </span>
                      )}
                    </div>
                    <button
                      className="billing-btn billing-btn--primary"
                      onClick={selectCustom}
                      disabled={!customValid || intentLoading}
                    >
                      {intentLoading ? "Loading..." : "Continue"}
                    </button>
                  </div>
                </div>
              )}

              {tab === "history" && (
                <div className="billing-history">
                  {loading && <div className="runs-empty">Loading…</div>}
                  {!loading && transactions.length === 0 && (
                    <div className="runs-empty">
                      <span>No transactions yet.</span>
                    </div>
                  )}
                  {!loading && transactions.length > 0 && (
                    <div className="billing-txns">
                      {transactions.map((t) => (
                        <div className="billing-txn" key={t.id}>
                          <div className="billing-txn__left">
                            <span className="billing-txn__desc">{t.description || "Top up"}</span>
                            <span className="billing-txn__date">{formatDate(t.created_at)}</span>
                          </div>
                          <div className="billing-txn__right">
                            <span className="billing-txn__amount">{formatCurrency(t.amount, t.currency)}</span>
                            <span className="billing-txn__fills">+{t.form_fills_purchased} fills</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}