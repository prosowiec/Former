import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Unverifiedpage from "./Unverifiedpage";

export default function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="spinner spinner--dark" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  console.log(user)
  if (user.email_verified === false) return <Unverifiedpage />;

  return children;
}