import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";

import PrivateRoute  from "./components/PrivateRoute";
import PublicRoute   from "./components/PublicRoute";
import LandingPage   from "./components/LandingPage";
import LoginPage     from "./components/LoginPage";
import OAuthSuccess  from "./components/OAuthSuccess";
import Dashboard     from "./components/Dashboard";
import VerifyEmail   from "./components/VerifyEmail";
import ResetPassword from "./components/ResetPassword";

import "./index.css";

export default function App() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Root — redirect based on auth state */}
      <Route
        path="/"
        element={<Navigate to={user ? "/home" : "/landing"} replace />}
      />

      {/* Public-only routes — redirect logged-in users to /home */}
      <Route
        path="/landing"
        element={
          <PublicRoute>
            <LandingPage />
          </PublicRoute>
        }
      />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      {/* OAuth callback */}
      <Route path="/oauth-success" element={<OAuthSuccess />} />

      {/* Email flows — public, no auth needed */}
      <Route path="/verify-email"   element={<VerifyEmail />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Private routes — redirect unauthenticated users to /login */}
      <Route
        path="/home"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to={user ? "/home" : "/landing"} replace />} />
    </Routes>
  );
}