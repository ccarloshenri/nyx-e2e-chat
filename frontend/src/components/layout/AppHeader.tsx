import { Button } from "../ui/Button";

type AppHeaderProps = {
  username: string;
  onRefresh: () => void;
  onLogout: () => void;
};

export function AppHeader({ username, onRefresh, onLogout }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div>
        <span className="eyebrow">Nyx</span>
        <h1>Private conversations</h1>
        <p className="muted">Signed in as {username}</p>
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
