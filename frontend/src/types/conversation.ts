export type ConversationSummary = {
  id: string;
  title: string;
  preview: string;
  updatedAt: string;
  unreadCount: number;
  participantLabel: string;
};

export type CreateConversationPayload = {
  target_username: string;
};
