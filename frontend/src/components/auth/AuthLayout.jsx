import { Link } from "react-router-dom";
import {
  Bot,
  CheckCircle2,
  MessageSquare,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";

import BrandMark from "../saas/BrandMark";

export default function AuthLayout({
  title,
  subtitle,
  children,
  footer,
  variant = "auth",
  stepLabel,
  sideTitle,
  sideItems,
}) {
  const isOnboarding = variant === "onboarding";

  return (
    <div className={`saas-page auth-page auth-page--${variant}`}>
      <div className="auth-split">
        <aside className="auth-split__panel" aria-hidden={!isOnboarding}>
          <Link to="/" className="auth-split__brand">
            <BrandMark />
          </Link>

          {isOnboarding ? (
            <>
              <p className="auth-split__step">{stepLabel || "Step 1 of 1"}</p>
              <h2 className="auth-split__title">
                {sideTitle || "Set up your business assistant"}
              </h2>
              <ul className="auth-split__list">
                {(sideItems || defaultOnboardingItems).map((item) => (
                  <li key={item}>
                    <CheckCircle2 size={18} aria-hidden="true" />
                    {item}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <>
              <p className="auth-split__eyebrow">
                <Sparkles size={16} aria-hidden="true" />
                Business Assistant SaaS
              </p>
              <h2 className="auth-split__title">
                Run your business conversations with clarity
              </h2>
              <p className="auth-split__desc">
                Capture customer messages, organize orders, and prepare for
                AI-assisted WhatsApp operations — without technical setup.
              </p>
              <ul className="auth-split__features">
                <li>
                  <MessageSquare size={18} aria-hidden="true" />
                  WhatsApp-first customer communication
                </li>
                <li>
                  <Bot size={18} aria-hidden="true" />
                  AI-ready business workflows
                </li>
                <li>
                  <Shield size={18} aria-hidden="true" />
                  Secure account and session handling
                </li>
                <li>
                  <Zap size={18} aria-hidden="true" />
                  Simple onboarding in minutes
                </li>
              </ul>
            </>
          )}
        </aside>

        <div className="auth-split__form">
          <div className="auth-card saas-animate-in">
            <div className="auth-card-header">
              <h1>{title}</h1>
              {subtitle ? <p>{subtitle}</p> : null}
            </div>

            {children}
          </div>

          {footer ? <div className="auth-footer">{footer}</div> : null}
        </div>
      </div>
    </div>
  );
}

const defaultOnboardingItems = [
  "Your business details are saved securely",
  "WhatsApp connection is the next step",
  "Assistant activation follows after connection",
];
