import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";

import BrandMark from "./BrandMark";

export default function SaasNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <header className={`saas-navbar ${scrolled ? "saas-navbar--scrolled" : ""}`}>
      <div className="saas-container saas-navbar__inner">
        <Link to="/" className="saas-navbar__brand" aria-label="NH home">
          <BrandMark />
        </Link>

        <button
          type="button"
          className="saas-navbar__toggle"
          aria-expanded={mobileOpen}
          aria-controls="saas-nav-menu"
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          <span className="sr-only">Toggle navigation</span>
        </button>

        <nav
          id="saas-nav-menu"
          className={`saas-navbar__links ${mobileOpen ? "saas-navbar__links--open" : ""}`}
          aria-label="Primary"
        >
          <a href="/#how-it-works">How It Works</a>
          <Link to="/login" className="saas-btn saas-btn-secondary saas-btn-sm">
            Login
          </Link>
          <Link to="/signup" className="saas-btn saas-btn-primary saas-btn-sm">
            Get Started
          </Link>
        </nav>
      </div>
    </header>
  );
}
