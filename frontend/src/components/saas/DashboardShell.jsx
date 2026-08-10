import { Link, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

import BrandMark from "./BrandMark";
import { useAuth } from "../../context/AuthContext";

export default function DashboardShell({ children }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="saas-page dashboard-page">
      <header className="dashboard-header">
        <div className="saas-container dashboard-header__inner">
          <Link to="/" className="saas-navbar__brand">
            <BrandMark />
          </Link>

          <div className="dashboard-header__actions">
            <span className="dashboard-user">{user?.full_name}</span>
            <button
              type="button"
              className="saas-btn saas-btn-ghost saas-btn-sm"
              onClick={handleLogout}
            >
              <LogOut size={16} aria-hidden="true" />
              Log Out
            </button>
          </div>
        </div>
      </header>

      <main className="saas-container dashboard-main">{children}</main>
    </div>
  );
}
