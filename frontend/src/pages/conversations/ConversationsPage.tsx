import { useEffect, useState } from "react";
import { AppHeader } from "../../components/layout/AppHeader";
import { ConversationList } from "../../components/conversation/ConversationList";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
import { useAuth } from "../../hooks/useAuth";
import { conversationService } from "../../services/conversations/conversationService";
import type { ConversationSummary } from "../../types/conversation";

export function ConversationsPage() {
  const { token, user, logout } = useAuth();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [targetUsername, setTargetUsername] = useState("");
  const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
  const [createSuccessMessage, setCreateSuccessMessage] = useState<string | null>(null);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);

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

  async function handleCreateConversation() {
    if (!token) {
      return;
    }

    const normalizedUsername = targetUsername.trim();
    if (!normalizedUsername) {
      setCreateErrorMessage("target_username_required");
      setCreateSuccessMessage(null);
      return;
    }

    setIsCreatingConversation(true);
    setCreateErrorMessage(null);
    setCreateSuccessMessage(null);

    try {
      await conversationService.createConversation(token, {
        target_username: normalizedUsername
      });
      setTargetUsername("");
      setCreateSuccessMessage("conversation_created");
      await loadConversations();
    } catch (error) {
      setCreateErrorMessage(
        error instanceof Error ? error.message : "unable_to_create_conversation"
      );
    } finally {
      setIsCreatingConversation(false);
    }
  }

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
          <div className="sidebar-card">
            <span className="eyebrow">New conversation</span>
            <h2>Start by username</h2>
            <p>Enter the username to create or reopen a direct conversation.</p>
            <div className="auth-form sidebar-form">
              <InputField
                id="target-username"
                label="Username"
                placeholder="bob"
                value={targetUsername}
                onChange={(event) => setTargetUsername(event.target.value)}
                autoComplete="off"
                required
              />
              {createErrorMessage ? <div className="banner-error">{createErrorMessage}</div> : null}
              {createSuccessMessage ? <div className="banner-success">{createSuccessMessage}</div> : null}
              <Button
                type="button"
                variant="secondary"
                fullWidth
                disabled={isCreatingConversation}
                onClick={() => void handleCreateConversation()}
              >
                {isCreatingConversation ? "Creating..." : "Create conversation"}
              </Button>
            </div>
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
