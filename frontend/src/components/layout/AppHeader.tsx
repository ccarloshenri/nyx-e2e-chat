import { Button } from "../ui/Button";
import { NyxLogo } from "../branding/NyxLogo";

type AppHeaderProps = {
  onRefresh: () => void;
  onLogout: () => void;
};

export function AppHeader({
  onRefresh,
  onLogout
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="header-actions header-actions-left">
        <Button
          variant="secondary"
          className="icon-button"
          onClick={onRefresh}
          aria-label="Refresh chats"
          title="Refresh chats"
        >
          <svg
            className="button-icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
            focusable="false"
          >
            <path
              d="M20 12a8 8 0 1 1-2.34-5.66"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
            <path
              d="M20 4v6h-6"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </Button>
      </div>
      <div className="app-header-brand app-header-brand-center">
        <NyxLogo className="brand-logo brand-logo-header" tone="white" />
      </div>
      <div className="header-actions header-actions-right">
        <Button variant="ghost" onClick={onLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
