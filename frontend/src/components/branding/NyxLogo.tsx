type NyxLogoProps = {
  className?: string;
  tone?: "white" | "purple";
  title?: string;
};

export function NyxLogo({
  className = "",
  tone = "white",
  title = "Nyx logo"
}: NyxLogoProps) {
  const stroke = tone === "purple" ? "rgb(139, 92, 246)" : "#ffffff";
  const fill = tone === "purple" ? "rgba(139, 92, 246, 0.18)" : "rgba(255, 255, 255, 0.12)";

  return (
    <svg
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <path
        d="M32 8c7.6 5 15.5 7.2 24 8.8-.1 17.1-5.9 30.3-24 39.2C13.9 47.1 8.1 33.9 8 16.8 16.5 15.2 24.4 13 32 8Z"
        fill={fill}
        stroke={stroke}
        strokeWidth="3.4"
        strokeLinejoin="round"
      />
      <path
        d="M32 22.4a6.2 6.2 0 0 1 4.7 10.3l1.7 8.9h-12.8l1.7-8.9A6.2 6.2 0 0 1 32 22.4Z"
        fill={stroke}
      />
      <path
        d="M18 40.8c7.5-2.7 14.3-7.2 20.4-13.4"
        fill="none"
        stroke={stroke}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
