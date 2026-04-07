import { Button } from "../ui/Button";

type AppHeaderProps = {
  username: string;
  conversationCount: number;
  unreadCount: number;
  onRefresh: () => void;
  onLogout: () => void;
};

export function AppHeader({
  username,
  conversationCount,
  unreadCount,
  onRefresh,
  onLogout
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-brand">
        <div>
          <span className="eyebrow">Nyx</span>
          <h1>Private conversations</h1>
          <p className="muted">Signed in as {username}</p>
          <div className="header-status-row">
            <span className="status-pill">Secure sync active</span>
            <span className="status-pill subtle">{conversationCount} threads</span>
            <span className="status-pill subtle">{unreadCount} unread</span>
          </div>
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
