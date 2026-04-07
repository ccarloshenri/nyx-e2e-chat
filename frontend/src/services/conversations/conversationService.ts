import { apiClient } from "../api/apiClient";
import type { ConversationSummary } from "../../types/conversation";
import { env } from "../../utils/env";

const conversationsMock: ConversationSummary[] = [
  {
    id: "conv-1",
    title: "Lena",
    preview: "New encrypted session available",
    updatedAt: "2026-04-05T17:40:00Z",
    unreadCount: 2,
    participantLabel: "Direct message"
  },
  {
    id: "conv-2",
    title: "Security Review",
    preview: "Keys rotated successfully",
    updatedAt: "2026-04-04T21:15:00Z",
    unreadCount: 0,
    participantLabel: "Team space"
  }
];

async function fetchMockConversations(): Promise<ConversationSummary[]> {
  return Promise.resolve(conversationsMock);
}

async function fetchBackendConversations(token: string): Promise<ConversationSummary[]> {
  const response = await apiClient.request<{ data: { conversations: ConversationSummary[] } }>(
    "/conversations",
    {
      method: "GET",
      token
    }
  );

  return response.data.conversations;
}

async function listConversations(token: string): Promise<ConversationSummary[]> {
  if (env.conversationsSource === "api") {
    return fetchBackendConversations(token);
  }

  return fetchMockConversations();
}

export const conversationService = {
  listConversations
};
