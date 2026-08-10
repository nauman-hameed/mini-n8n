import { Link } from "react-router-dom";

import Logo from "../components/Logo";

export default function LandingPage() {
  return (
    <div className="saas-page landing-page">
      <header className="saas-nav">
        <Link to="/" className="saas-nav-brand">
          <Logo />
          <span>Hoplynk Assistant</span>
        </Link>

        <nav className="saas-nav-links" aria-label="Primary">
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <Link to="/login">Login</Link>
          <Link to="/signup" className="saas-btn saas-btn-primary">
            Get Started
          </Link>
        </nav>
      </header>

      <main>
        <section className="saas-hero">
          <div className="saas-hero-copy">
            <p className="saas-eyebrow">AI Business Assistant</p>
            <h1>Your AI Business Assistant for WhatsApp</h1>
            <p className="saas-lead">
              Help your business stay responsive, organized, and ready to grow.
              Hoplynk Assistant is being built to manage customer conversations,
              orders, and routine operations through WhatsApp — without the
              complexity of manual setup.
            </p>
            <div className="saas-hero-actions">
              <Link to="/signup" className="saas-btn saas-btn-primary saas-btn-lg">
                Get Started
              </Link>
              <a href="#how-it-works" className="saas-btn saas-btn-secondary saas-btn-lg">
                See How It Works
              </a>
            </div>
          </div>

          <div className="saas-hero-preview" aria-hidden="true">
            <div className="preview-card">
              <div className="preview-card-header">
                <span>Business Overview</span>
                <span className="preview-pill">Setup in progress</span>
              </div>
              <div className="preview-stat-grid">
                <div>
                  <strong>WhatsApp</strong>
                  <span>Customer channel</span>
                </div>
                <div>
                  <strong>Orders</strong>
                  <span>Structured automatically</span>
                </div>
                <div>
                  <strong>Assistant</strong>
                  <span>Always on</span>
                </div>
              </div>
              <div className="preview-chat">
                <div className="preview-message incoming">
                  Hi, I&apos;d like 2 shirts and 1 pair of shoes.
                </div>
                <div className="preview-message outgoing">
                  Thanks — we&apos;ve received your order and will confirm shortly.
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="saas-section" id="features">
          <div className="saas-section-header">
            <p className="saas-eyebrow">Product Benefits</p>
            <h2>Built for business owners, not automation engineers</h2>
            <p>
              Hoplynk Assistant is designed to feel like a polished SaaS product —
              simple to start, clear to use, and focused on outcomes.
            </p>
          </div>

          <div className="saas-feature-grid">
            <article className="saas-feature-card">
              <h3>Automate customer conversations</h3>
              <p>
                Reduce the time spent answering repetitive WhatsApp messages and
                keep customers informed.
              </p>
            </article>
            <article className="saas-feature-card">
              <h3>Handle customer orders</h3>
              <p>
                Turn unstructured messages into organized business information your
                team can act on.
              </p>
            </article>
            <article className="saas-feature-card">
              <h3>Reduce repetitive work</h3>
              <p>
                Let your assistant take care of routine operational tasks so you can
                focus on growth.
              </p>
            </article>
            <article className="saas-feature-card">
              <h3>Keep operations organized</h3>
              <p>
                Bring customer activity into one clear place instead of scattered
                chats and notes.
              </p>
            </article>
            <article className="saas-feature-card">
              <h3>AI-powered assistance</h3>
              <p>
                Use AI to understand customer intent and support smarter business
                responses over time.
              </p>
            </article>
            <article className="saas-feature-card">
              <h3>WhatsApp-first communication</h3>
              <p>
                Meet customers where they already are — on the channel they use every
                day.
              </p>
            </article>
          </div>
        </section>

        <section className="saas-section saas-section-muted" id="how-it-works">
          <div className="saas-section-header">
            <p className="saas-eyebrow">How It Works</p>
            <h2>Get started in four simple steps</h2>
          </div>

          <ol className="saas-steps">
            <li>
              <span>1</span>
              <div>
                <h3>Create your account</h3>
                <p>Sign up with your name, email, and password.</p>
              </div>
            </li>
            <li>
              <span>2</span>
              <div>
                <h3>Add your business</h3>
                <p>Tell us your business name so we can personalize your setup.</p>
              </div>
            </li>
            <li>
              <span>3</span>
              <div>
                <h3>Connect WhatsApp</h3>
                <p>
                  For this milestone, you&apos;ll provide the WhatsApp number you want
                  to use. Full Meta connection comes next.
                </p>
              </div>
            </li>
            <li>
              <span>4</span>
              <div>
                <h3>Your assistant becomes ready</h3>
                <p>
                  Once connected, your assistant will handle business operations
                  automatically behind the scenes.
                </p>
              </div>
            </li>
          </ol>
        </section>

        <section className="saas-cta">
          <div>
            <h2>Ready to set up your Business Assistant?</h2>
            <p>Create your account and complete your initial business setup in minutes.</p>
          </div>
          <Link to="/signup" className="saas-btn saas-btn-primary saas-btn-lg">
            Create Account
          </Link>
        </section>
      </main>

      <footer className="saas-footer">
        <div>
          <strong>Hoplynk Assistant</strong>
          <p>AI-powered business operations for WhatsApp-first businesses.</p>
        </div>
        <div className="saas-footer-links">
          <Link to="/login">Login</Link>
          <Link to="/signup">Get Started</Link>
        </div>
      </footer>
    </div>
  );
}
