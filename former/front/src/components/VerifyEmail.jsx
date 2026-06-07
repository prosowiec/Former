import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api } from "../api/client";

export default function VerifyEmail() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const [status, setStatus] = useState("verifying"); // verifying | success | error | no-token
  const [error,  setError]  = useState(null);

  useEffect(() => {
    const token = new URLSearchParams(location.search).get("token");
    if (!token) { setStatus("no-token"); return; }

    api.verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => { setError(err.message); setStatus("error"); });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="login-page">
      <div className="login-card" style={{ gap: "16px", textAlign: "center" }}>
        <span className="logo">former</span>

        {status === "verifying" && (
          <>
            <span className="spinner spinner--dark" style={{ alignSelf: "center" }} />
            <p className="login-desc">Verifying your email…</p>
          </>
        )}

        {status === "success" && (
          <>
            <span style={{ fontSize: 36 }}>✓</span>
            <p className="login-desc">Email verified! You can now sign in.</p>
            <button className="submit-btn submit-btn--full" onClick={() => navigate("/login")}>
              Go to sign in
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <span style={{ fontSize: 36 }}>✗</span>
            <p className="login-desc" style={{ color: "var(--red)" }}>
              {error ?? "Verification failed. The link may have expired."}
            </p>
            <button className="submit-btn submit-btn--full" onClick={() => navigate("/login")}>
              Back to sign in
            </button>
          </>
        )}

        {status === "no-token" && (
          <>
            <p className="login-desc" style={{ color: "var(--red)" }}>
              No verification token found in the URL.
            </p>
            <button className="submit-btn submit-btn--full" onClick={() => navigate("/login")}>
              Back to sign in
            </button>
          </>
        )}
      </div>
    </div>
  );
}