import type { ConversationSummary } from "../../types/conversation";
import { formatTimestamp } from "../../utils/date";

type ConversationListProps = {
  conversations: ConversationSummary[];
  isLoading: boolean;
  errorMessage: string | null;
};

export function ConversationList({
  conversations,
  isLoading,
  errorMessage
}: ConversationListProps) {
  if (isLoading) {
    return <div className="panel-state">Loading conversations...</div>;
  }

  if (errorMessage) {
    return <div className="panel-state error-state">{errorMessage}</div>;
  }

  if (!conversations.length) {
    return (
      <div className="panel-state">
        <h2>No conversations yet</h2>
        <p>Your secure threads will appear here as soon as they are available.</p>
      </div>
    );
  }

  return (
    <ul className="conversation-list">
      {conversations.map((conversation) => (
        <li className="conversation-card" key={conversation.id}>
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
              <span className="muted">All caught up</span>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
