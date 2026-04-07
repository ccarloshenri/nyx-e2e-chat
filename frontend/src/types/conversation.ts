export type ConversationSummary = {
  id: string;
  title: string;
  preview: string;
  updatedAt: string;
  unreadCount: number;
  participantLabel: string;
  hasStoredSecret: boolean;
};

export type CreateConversationPayload = {
  target_username: string;
  conversation_password_salt: string;
  conversation_password_kdf_params: Record<string, unknown>;
  unlock_check_ciphertext: string;
  unlock_check_nonce: string;
  creator_access: {
    encrypted_conversation_password: string;
    nonce: string;
  };
};

export type ConversationAccessContext = {
  conversation_id: string;
  conversation_password_salt: string;
  conversation_password_kdf_params: Record<string, unknown>;
  unlock_check_ciphertext: string;
  unlock_check_nonce: string;
  participant_access: {
    encrypted_conversation_password: string;
    nonce: string;
  } | null;
  has_stored_secret: boolean;
};

export type SaveConversationAccessPayload = {
  encrypted_conversation_password: string;
  nonce: string;
};
