import { Button } from "../ui/Button";
import { Logo } from "../ui/Logo";

type AppHeaderProps = {
  username: string;
  onRefresh: () => void;
  onLogout: () => void;
};

export function AppHeader({ username, onRefresh, onLogout }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-brand">
        <Logo size={44} className="nyx-logo header-logo" />
        <div>
          <span className="eyebrow">Nyx</span>
          <h1>Private conversations</h1>
          <p className="muted">Signed in as {username}</p>
        </div>
      </div>
      <div className="header-actions">
        <Button variant="secondary" onClick={onRefresh}>
          Refresh
        </Button>
        <Button variant="ghost" onClick={onLogout}>
          Logout
        </Button>
      </div>
    </header>
  );
}
