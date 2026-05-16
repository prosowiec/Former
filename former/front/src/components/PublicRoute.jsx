import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="spinner spinner--dark" />
      </div>
    );
  }

  return user ? <Navigate to="/home" replace /> : children;
}