import { useEffect, useState } from "react";
import { AppHeader } from "../../components/layout/AppHeader";
import { ConversationList } from "../../components/conversation/ConversationList";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
import { useAuth } from "../../hooks/useAuth";
import { conversationService } from "../../services/conversations/conversationService";
import type { ConversationSummary } from "../../types/conversation";
import { formatTimestamp } from "../../utils/date";

export function ConversationsPage() {
  const { token, user, logout } = useAuth();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [targetUsername, setTargetUsername] = useState("");
  const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
  const [createSuccessMessage, setCreateSuccessMessage] = useState<string | null>(null);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const unreadCount = conversations.reduce((total, conversation) => total + conversation.unreadCount, 0);
  const selectedConversation =
    conversations.find((conversation) => conversation.id === selectedConversationId) ??
    conversations[0] ??
    null;

  async function loadConversations() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const nextConversations = await conversationService.listConversations(token);
      setConversations(nextConversations);
      setSelectedConversationId((currentSelectedConversationId) => {
        if (
          currentSelectedConversationId &&
          nextConversations.some((conversation) => conversation.id === currentSelectedConversationId)
        ) {
          return currentSelectedConversationId;
        }

        return nextConversations[0]?.id ?? null;
      });
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
        conversationCount={conversations.length}
        unreadCount={unreadCount}
        onRefresh={() => void loadConversations()}
        onLogout={logout}
      />
      <section className="conversations-grid">
        <aside className="conversation-sidebar inbox-sidebar">
          <div className="sidebar-card inbox-card">
            <div className="sidebar-card-heading">
              <div>
                <span className="eyebrow">Inbox</span>
                <h2>Your secure threads</h2>
              </div>
              <span className="sidebar-counter">{conversations.length}</span>
            </div>
            <p>
              Client-side encryption stays active across your conversation list and message
              previews.
            </p>
            <ConversationList
              conversations={conversations}
              isLoading={isLoading}
              errorMessage={errorMessage}
              selectedConversationId={selectedConversation?.id ?? null}
              onSelectConversation={setSelectedConversationId}
            />
          </div>
          <div className="sidebar-card composer-card">
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
        <section className="conversation-panel chat-panel">
          {selectedConversation ? (
            <>
              <div className="chat-panel-header">
                <div className="chat-identity">
                  <span className="conversation-avatar conversation-avatar-large" aria-hidden="true">
                    {selectedConversation.participantLabel.slice(0, 2).toUpperCase()}
                  </span>
                  <div>
                    <span className="eyebrow">Active thread</span>
                    <h2>{selectedConversation.title}</h2>
                    <p className="muted">
                      Last activity {formatTimestamp(selectedConversation.updatedAt)} ·{" "}
                      {selectedConversation.participantLabel}
                    </p>
                  </div>
                </div>
                <div className="chat-security-badge">End-to-end protected</div>
              </div>

              <div className="chat-timeline">
                <div className="message-row">
                  <div className="message-bubble message-bubble-received">
                    <span className="message-label">Latest encrypted preview</span>
                    <p>{selectedConversation.preview}</p>
                    <span className="message-meta">
                      {selectedConversation.participantLabel} ·{" "}
                      {formatTimestamp(selectedConversation.updatedAt)}
                    </span>
                  </div>
                </div>

                <div className="message-row message-row-outgoing">
                  <div className="message-bubble message-bubble-sent">
                    <span className="message-label">Security status</span>
                    <p>
                      Messages in this workspace remain encrypted in the client before transport and
                      storage.
                    </p>
                    <span className="message-meta">Nyx client · Verified transport</span>
                  </div>
                </div>
              </div>

              <div className="chat-composer-shell">
                <div className="chat-composer-copy">
                  <span className="eyebrow">Composer</span>
                  <h3>Thread actions</h3>
                  <p>
                    Conversation creation is available now. Full in-thread message composition can
                    be layered on top of this workspace next.
                  </p>
                </div>
                <div className="chat-composer-actions">
                  <Button variant="secondary" onClick={() => void loadConversations()}>
                    Sync thread
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setTargetUsername(selectedConversation.participantLabel)}
                  >
                    Reopen by username
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="panel-state chat-empty-state">
              <span className="eyebrow">No active thread</span>
              <h2>Open or create a secure conversation</h2>
              <p>
                Select a thread from the inbox or create a new one to turn this workspace into your
                active encrypted chat surface.
              </p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
