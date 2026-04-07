import { EncryptionType } from "../../crypto";
import { apiClient } from "../api/apiClient";
import type {
  ConversationMessagesResponse,
  PendingMessagesResponse,
  SendMessagePayload,
  UserLookupResponse,
} from "../../types/message";

async function fetchUserByUsername(username: string, token: string) {
  const response = await apiClient.request<UserLookupResponse>("/auth/public-key", {
    method: "POST",
    token,
    body: { username },
  });

  return response.data;
}

async function sendMessage(token: string, payload: SendMessagePayload) {
  return apiClient.request("/messages", {
    method: "POST",
    token,
    body: payload,
  });
}

async function fetchPendingMessages(token: string) {
  const response = await apiClient.request<PendingMessagesResponse>("/messages/pending", {
    method: "GET",
    token,
  });

  return response.data.messages;
}

async function listConversationMessages(token: string, conversationId: string) {
  const response = await apiClient.request<ConversationMessagesResponse>(
    `/conversations/${conversationId}/messages`,
    {
      method: "GET",
      token,
    },
  );

  return response.data.messages;
}

async function acknowledgeMessage(
  token: string,
  payload: { conversation_id: string; message_id: string; received_at: string },
) {
  return apiClient.request("/messages/ack", {
    method: "POST",
    token,
    body: payload,
  });
}

export { EncryptionType };

export const messageService = {
  fetchUserByUsername,
  sendMessage,
  fetchPendingMessages,
  listConversationMessages,
  acknowledgeMessage,
};
