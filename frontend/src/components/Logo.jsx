function Logo() {
  return (
    <div className="logo" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="6" cy="12" r="3" fill="white" opacity="0.9" />
        <circle cx="18" cy="6" r="3" fill="white" opacity="0.7" />
        <circle cx="18" cy="18" r="3" fill="white" opacity="0.7" />
        <line x1="8.5" y1="11" x2="15.5" y2="7" stroke="white" strokeWidth="1.5" opacity="0.6" />
        <line x1="8.5" y1="13" x2="15.5" y2="17" stroke="white" strokeWidth="1.5" opacity="0.6" />
      </svg>
    </div>
  );
}

export default Logo;
