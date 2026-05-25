import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";

export function useBilling() {
  const [billing, setBilling] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBilling = useCallback(async () => {
    try {
      const [info, txns] = await Promise.all([
        api.getBillingInfo(),
        api.getTransactions(),
      ]);
      setBilling(info);
      setTransactions(txns);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBilling();
  }, [fetchBilling]);

  return { billing, transactions, loading, error, refetch: fetchBilling };
}