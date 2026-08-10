import { Link } from "react-router-dom";

import Logo from "../Logo";

export default function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}) {
  return (
    <div className="saas-page auth-page">
      <div className="auth-shell">
        <Link to="/" className="auth-brand">
          <Logo />
          <span>Hoplynk Assistant</span>
        </Link>

        <div className="auth-card">
          <div className="auth-card-header">
            <h1>{title}</h1>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>

          {children}
        </div>

        {footer ? <div className="auth-footer">{footer}</div> : null}
      </div>
    </div>
  );
}
