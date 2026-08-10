import Logo from "../Logo";

export default function BrandMark({ showText = true, size = "md" }) {
  return (
    <span className={`brand-mark brand-mark--${size}`}>
      <Logo />
      {showText ? <span className="brand-mark__text">Hoplynk</span> : null}
    </span>
  );
}
