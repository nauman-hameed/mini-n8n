import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function LoadingScreen() {
  return (
    <div className="saas-page">
      <div className="saas-loading">
        <Loader2 size={28} className="saas-spinner" aria-hidden="true" />
        <span>Loading…</span>
      </div>
    </div>
  );
}

export function PublicOnlyRoute() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (user) {
    const redirectTo = user.onboarding_completed ? "/dashboard" : "/onboarding";
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export function ProtectedRoute({ requireOnboardingComplete: _requireOnboardingComplete = false }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!user.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}

export function OnboardingRoute() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (user.onboarding_completed) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
