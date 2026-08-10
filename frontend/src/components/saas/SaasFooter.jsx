import { Link } from "react-router-dom";

import BrandMark from "./BrandMark";

export default function SaasFooter() {
  return (
    <footer className="saas-footer">
      <div className="saas-container saas-footer__grid">
        <div className="saas-footer__brand">
          <BrandMark />
          <p>AI-powered business operations for WhatsApp-first businesses.</p>
        </div>

        <div className="saas-footer__col">
          <h3>Product</h3>
          <Link to="/signup">Get Started</Link>
          <Link to="/login">Login</Link>
          <a href="/#features">Features</a>
        </div>

        <div className="saas-footer__col">
          <h3>Legal</h3>
          <span className="saas-footer__placeholder">Privacy</span>
          <span className="saas-footer__placeholder">Terms</span>
        </div>

        <div className="saas-footer__col">
          <h3>Support</h3>
          <span className="saas-footer__placeholder">Contact</span>
        </div>
      </div>

      <div className="saas-container saas-footer__bottom">
        <p>© {new Date().getFullYear()} Hoplynk Assistant. All rights reserved.</p>
      </div>
    </footer>
  );
}
