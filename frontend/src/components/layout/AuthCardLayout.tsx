import type { PropsWithChildren } from "react";
import { NyxLogo } from "../branding/NyxLogo";

type AuthCardLayoutProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
}>;

export function AuthCardLayout({
  eyebrow,
  title,
  description,
  children
}: AuthCardLayoutProps) {
  return (
    <div className="auth-shell">
      <div className="auth-brand">
        <NyxLogo className="brand-logo brand-logo-auth" tone="white" />
      </div>
      <div className="auth-panel">
        <div className="auth-copy">
          <span className="eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {children}
      </div>
    </div>
  );
}
