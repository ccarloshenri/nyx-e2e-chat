import type { ConversationSummary } from "../../types/conversation";
import { formatTimestamp } from "../../utils/date";

type ConversationListProps = {
  conversations: ConversationSummary[];
  isLoading: boolean;
  errorMessage: string | null;
  selectedConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
};

export function ConversationList({
  conversations,
  isLoading,
  errorMessage,
  selectedConversationId,
  onSelectConversation
}: ConversationListProps) {
  if (isLoading) {
    return <div className="panel-state">Loading chats...</div>;
  }

  if (errorMessage) {
    return <div className="panel-state error-state">{errorMessage}</div>;
  }

  if (!conversations.length) {
    return (
      <div className="panel-state">
        <h2>No chats yet</h2>
        <p>Your conversations will appear here.</p>
      </div>
    );
  }

  return (
    <ul className="conversation-list">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <button
            type="button"
            className={`conversation-card ${
              selectedConversationId === conversation.id ? "conversation-card-active" : ""
            }`.trim()}
            onClick={() => onSelectConversation(conversation.id)}
          >
            <span className="conversation-avatar" aria-hidden="true">
              {conversation.participantLabel.slice(0, 2).toUpperCase()}
            </span>
            <div className="conversation-card-body">
              <div className="conversation-main">
                <div>
                  <h2>{conversation.title}</h2>
                  <p>{conversation.preview}</p>
                </div>
                <span className="conversation-time">
                  {formatTimestamp(conversation.updatedAt)}
                </span>
              </div>
              <div className="conversation-meta">
                <span>{conversation.participantLabel}</span>
                {conversation.unreadCount > 0 ? (
                  <span className="unread-badge">{conversation.unreadCount}</span>
                ) : (
                  <span className="muted">{conversation.hasStoredSecret ? "Ready" : "New"}</span>
                )}
              </div>
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
