import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function HealthBadge() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    api
      .health()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <span className={`health-badge health-badge--${status}`}>
      <span className="health-dot" />
      {status === "checking" ? "checking" : status === "ok" ? "API online" : "API offline"}
    </span>
  );
}