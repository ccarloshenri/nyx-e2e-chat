import { useEffect, useState } from "react";
import { AppHeader } from "../../components/layout/AppHeader";
import { ConversationList } from "../../components/conversation/ConversationList";
import { useAuth } from "../../hooks/useAuth";
import { conversationService } from "../../services/conversations/conversationService";
import type { ConversationSummary } from "../../types/conversation";

export function ConversationsPage() {
  const { token, user, logout } = useAuth();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadConversations() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const nextConversations = await conversationService.listConversations(token);
      setConversations(nextConversations);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to load conversations right now."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadConversations();
  }, [token]);

  return (
    <main className="app-shell">
      <AppHeader
        username={user?.username ?? "unknown"}
        onRefresh={() => void loadConversations()}
        onLogout={logout}
      />
      <section className="conversations-grid">
        <aside className="conversation-sidebar">
          <div className="sidebar-card">
            <span className="eyebrow">Privacy status</span>
            <h2>Secure transport enabled</h2>
            <p>
              Message encryption and decryption are resolved only in the frontend through
              client-side encryption strategies. The backend stores and forwards encrypted payloads
              without access to plaintext.
            </p>
          </div>
        </aside>
        <section className="conversation-panel">
          <ConversationList
            conversations={conversations}
            isLoading={isLoading}
            errorMessage={errorMessage}
          />
        </section>
      </section>
    </main>
  );
}
