import Logo from "./Logo";

function LandingPage({ onOpenEditor }) {
  return (
    <div className="landing">
      <div className="landing-grid" aria-hidden="true" />
      <div className="landing-glow" aria-hidden="true" />

      <nav className="landing-nav">
        <div className="landing-nav-brand">
          <Logo />
          <span className="landing-nav-title">mini-n8n</span>
          <span className="landing-nav-badge">Beta</span>
        </div>
        <button className="btn btn-primary" onClick={onOpenEditor}>
          Open Editor
        </button>
      </nav>

      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1>
            Automate workflows
            <br />
            <span>visually</span>
          </h1>
          <p className="landing-hero-desc">
            Build powerful automations with a drag-and-drop canvas. Connect
            WhatsApp, AI, Google Sheets, and APIs — just like n8n, but
            lightweight and self-hosted.
          </p>
          <div className="landing-hero-actions">
            <button className="btn btn-primary" onClick={onOpenEditor}>
              Start Building →
            </button>
            <button
              className="btn"
              onClick={() =>
                document
                  .getElementById("features")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Learn More
            </button>
          </div>
        </div>

        <div className="landing-preview">
          <div className="landing-preview-window">
            <div className="landing-preview-bar">
              <span className="preview-dot preview-dot-red" />
              <span className="preview-dot preview-dot-yellow" />
              <span className="preview-dot preview-dot-green" />
            </div>
            <div className="landing-preview-canvas">
              <div className="preview-node">
                <span
                  className="preview-node-icon"
                  style={{ background: "rgba(37, 211, 102, 0.2)" }}
                >
                  💬
                </span>
                WhatsApp Trigger
              </div>
              <span className="preview-arrow">→</span>
              <div className="preview-node">
                <span
                  className="preview-node-icon"
                  style={{ background: "rgba(192, 132, 252, 0.2)" }}
                >
                  ✨
                </span>
                AI Extractor
              </div>
              <span className="preview-arrow">→</span>
              <div className="preview-node">
                <span
                  className="preview-node-icon"
                  style={{ background: "rgba(52, 168, 83, 0.2)" }}
                >
                  📊
                </span>
                Google Sheets
              </div>
              <span className="preview-arrow">→</span>
              <div className="preview-node">
                <span
                  className="preview-node-icon"
                  style={{ background: "rgba(37, 211, 102, 0.2)" }}
                >
                  📤
                </span>
                WhatsApp Reply
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-features" id="features">
        <p className="landing-features-title">What you can build</p>
        <div className="landing-features-grid">
          <div className="feature-card">
            <div
              className="feature-card-icon"
              style={{ background: "rgba(37, 211, 102, 0.15)" }}
            >
              💬
            </div>
            <h3>WhatsApp Automation</h3>
            <p>
              Trigger workflows from incoming messages and send personalized
              replies back to customers automatically.
            </p>
          </div>
          <div className="feature-card">
            <div
              className="feature-card-icon"
              style={{ background: "rgba(192, 132, 252, 0.15)" }}
            >
              ✨
            </div>
            <h3>AI Order Extraction</h3>
            <p>
              Use local LLMs via Ollama to parse unstructured order messages
              into structured name, phone, address, and items.
            </p>
          </div>
          <div className="feature-card">
            <div
              className="feature-card-icon"
              style={{ background: "rgba(52, 168, 83, 0.15)" }}
            >
              📊
            </div>
            <h3>Google Sheets Sync</h3>
            <p>
              Append extracted orders directly to your spreadsheet with OAuth
              — no copy-paste needed.
            </p>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        mini-n8n — a lightweight workflow automation builder
      </footer>
    </div>
  );
}

export default LandingPage;
