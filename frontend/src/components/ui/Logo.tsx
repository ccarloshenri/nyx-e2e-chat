import nyxLogo from "../../assets/images/nyx_logo.png";

type LogoProps = {
  size?: number;
  className?: string;
};

export function Logo({ size = 40, className }: LogoProps) {
  return (
    <span
      className={className}
      style={{ width: size, height: size }}
      aria-label="Nyx logo"
      role="img"
    >
      <img src={nyxLogo} alt="Nyx logo" className="nyx-logo-image" />
    </span>
  );
}
