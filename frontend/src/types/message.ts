export type PendingMessageRecord = {
  conversation_id: string;
  message_id: string;
  sender_id: string;
  recipient_id: string;
  encryption_type: string;
  ciphertext: string;
  encrypted_message_key: string;
  nonce: string;
  created_at: string;
  status: string;
  metadata?: Record<string, unknown>;
};

export type ConversationMessagesResponse = {
  success: boolean;
  data: {
    messages: PendingMessageRecord[];
    count: number;
  };
};

export type PendingMessagesResponse = {
  success: boolean;
  data: {
    messages: PendingMessageRecord[];
    count: number;
  };
};

export type SendMessagePayload = {
  conversation_id: string;
  sender_id: string;
  recipient_id: string;
  encryption_type: string;
  ciphertext: string;
  encrypted_message_key: string;
  nonce: string;
  message_id: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type ChatMessage = {
  id: string;
  conversationId: string;
  text: string;
  createdAt: string;
  direction: "incoming" | "outgoing";
  status: "pending" | "sent" | "failed";
  senderLabel: string;
};

export type UserLookupResponse = {
  success: boolean;
  data: {
    user_id: string;
    username: string;
    public_key: string;
  };
};
