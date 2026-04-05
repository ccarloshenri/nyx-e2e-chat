import { useAuth } from "../../hooks/useAuth";

export function ConversationsPage() {
  const { user, logout } = useAuth();

  return (
    <main className="screen-center">
      <div className="auth-panel">
        <span className="eyebrow">Nyx</span>
        <h1>Protected area</h1>
        <p className="muted">Signed in as {user?.username ?? "unknown"}.</p>
        <p className="muted">The conversations workspace will be added in the next delivery block.</p>
        <button className="button button-secondary" onClick={logout} type="button">
          Logout
        </button>
      </div>
    </main>
  );
}
