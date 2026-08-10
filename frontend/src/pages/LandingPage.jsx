import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardList,
  MessageCircle,
  Sparkles,
} from "lucide-react";

import SaasFooter from "../components/saas/SaasFooter";
import SaasNavbar from "../components/saas/SaasNavbar";

const STEPS = [
  {
    n: "01",
    title: "Create your account",
    desc: "Sign up with your name, email, and password in minutes.",
  },
  {
    n: "02",
    title: "Add your business",
    desc: "Tell us your business name and the WhatsApp number you plan to use.",
  },
  {
    n: "03",
    title: "Connect WhatsApp",
    desc: "Link your WhatsApp Business account — coming in the next release.",
  },
  {
    n: "04",
    title: "Activate your assistant",
    desc: "Your assistant handles conversations and operations behind the scenes.",
  },
];

const TRUST_ITEMS = [
  "Built for growing businesses",
  "Secure account setup",
  "Simple onboarding",
  "AI-assisted workflows",
];

export default function LandingPage() {
  return (
    <div className="saas-page landing-page">
      <SaasNavbar />

      <main>
        <section className="saas-hero">
          <div className="saas-container saas-hero__grid">
            <div className="saas-hero__copy saas-animate-in">
              <p className="saas-eyebrow">
                <Sparkles size={14} aria-hidden="true" />
                | // AI BUSINESS ASSISTANT |
              </p>
              <h1>Your AI Business Assistant for WhatsApp</h1>
              <p className="saas-lead">
                Handle customer messages, capture orders, and reduce repetitive
                work — with a polished assistant built for business owners, not
                automation engineers.
              </p>
              <div className="saas-hero__actions">
                <Link to="/signup" className="saas-btn saas-btn-primary saas-btn-lg">
                  Get Started
                  <ArrowRight size={18} aria-hidden="true" />
                </Link>
                <a href="#how-it-works" className="saas-btn saas-btn-secondary saas-btn-lg">
                  See How It Works
                </a>
              </div>
            </div>

            <div className="saas-hero__visual saas-animate-in saas-animate-delay-1" aria-hidden="true">
              <div className="hero-mock">
                <div className="hero-mock__chrome">
                  <span /><span /><span />
                  <p>NH // Live</p>
                </div>
                <div className="hero-mock__body">
                  <div className="hero-mock__stats">
                    <div>
                      <strong>12</strong>
                      <span>Messages today</span>
                    </div>
                    <div>
                      <strong>5</strong>
                      <span>Orders captured</span>
                    </div>
                    <div>
                      <strong>Live</strong>
                      <span>Assistant status</span>
                    </div>
                  </div>
                  <div className="hero-mock__chat">
                    <div className="hero-mock__msg hero-mock__msg--in">
                      Hi, I&apos;d like 2 shirts and 1 pair of shoes.
                    </div>
                    <div className="hero-mock__msg hero-mock__msg--out">
                      Thanks — we&apos;ve captured your order details.
                    </div>
                    <div className="hero-mock__capture">
                      <CheckCircle2 size={14} />
                      Order structured · Name · Items · Phone
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <div className="saas-container trust-strip__inner">
            {TRUST_ITEMS.map((item) => (
              <span key={item}>
                <CheckCircle2 size={16} aria-hidden="true" />
                {item}
              </span>
            ))}
          </div>
        </section>

        <section className="saas-section saas-section--muted" id="how-it-works">
          <div className="saas-container">
            <div className="saas-section-header saas-reveal">
              <p className="saas-eyebrow">01 — How It Works</p>
              <h2>From signup to assistant in four steps</h2>
            </div>

            <ol className="steps-grid">
              {STEPS.map((step) => (
                <li key={step.n} className="step-card saas-reveal">
                  <span className="step-card__num">{step.n}</span>
                  <h3>{step.title}</h3>
                  <p>{step.desc}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="saas-section">
          <div className="saas-container use-case saas-reveal">
            <div className="use-case__copy">
              <p className="saas-eyebrow">02 — Use Case</p>
              <h2>From customer message to organized business data</h2>
              <p>
                Illustrative preview of how NH will help you understand
                requests, capture details, and keep operations clear.
              </p>
            </div>
            <div className="use-case__flow" aria-hidden="true">
              <div className="flow-step">
                <MessageCircle size={20} />
                <div>
                  <strong>Customer messages you</strong>
                  <p>&quot;I want 2 blue shirts, deliver to Karachi.&quot;</p>
                </div>
              </div>
              <div className="flow-step">
                <Bot size={20} />
                <div>
                  <strong>Assistant understands</strong>
                  <p>Extracts intent, items, and contact details.</p>
                </div>
              </div>
              <div className="flow-step">
                <ClipboardList size={20} />
                <div>
                  <strong>Business stays organized</strong>
                  <p>Structured records ready for your team.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="saas-cta">
          <div className="saas-container saas-cta__inner saas-reveal">
            <div>
              <p className="saas-eyebrow">Ready when you are</p>
              <h2>Set up your business assistant in minutes</h2>
              <p>Create your account and complete initial business setup today.</p>
            </div>
            <Link to="/signup" className="saas-btn saas-btn-white saas-btn-lg">
              Get Started
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </section>
      </main>

      <SaasFooter />
    </div>
  );
}
