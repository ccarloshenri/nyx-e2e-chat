import { useEffect, useState } from "react";
import { ConversationList } from "../../components/conversation/ConversationList";
import { AppHeader } from "../../components/layout/AppHeader";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
import { EncryptionType } from "../../crypto";
import { useAuth } from "../../hooks/useAuth";
import { conversationService } from "../../services/conversations/conversationService";
import { createCryptoService } from "../../services/crypto/cryptoService";
import { messageService } from "../../services/messages/messageService";
import type { ConversationAccessContext, ConversationSummary } from "../../types/conversation";
import type { ChatMessage, PendingMessageRecord } from "../../types/message";
import { formatTimestamp } from "../../utils/date";
import { env } from "../../utils/env";

const cryptoService = createCryptoService();
const CONVERSATION_KDF_PARAMS = {
  algorithm: "PBKDF2",
  iterations: 310000,
  hash: "SHA-256",
};

type RecipientInfo = {
  userId: string;
  username: string;
};

function toBase64(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes));
}

export function ConversationsPage() {
  const {
    token,
    user,
    logout,
    hasMasterPasswordInMemory,
    unlockedConversationIds,
    getMasterPasswordFromMemory,
    rememberMasterPassword,
    getConversationKeyFromMemory,
    rememberConversationKey,
  } = useAuth();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [targetUsername, setTargetUsername] = useState("");
  const [isCreateChatOpen, setIsCreateChatOpen] = useState(false);
  const [createMasterPassword, setCreateMasterPassword] = useState("");
  const [createConversationPassword, setCreateConversationPassword] = useState("");
  const [confirmConversationPassword, setConfirmConversationPassword] = useState("");
  const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
  const [createSuccessMessage, setCreateSuccessMessage] = useState<string | null>(null);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const [conversationAccessContext, setConversationAccessContext] =
    useState<Record<string, ConversationAccessContext>>({});
  const [recipientInfoByConversation, setRecipientInfoByConversation] = useState<Record<string, RecipientInfo>>({});
  const [encryptedMessagesByConversation, setEncryptedMessagesByConversation] = useState<
    Record<string, PendingMessageRecord[]>
  >({});
  const [decryptedMessagesByConversation, setDecryptedMessagesByConversation] = useState<Record<string, ChatMessage[]>>(
    {},
  );
  const [unlockMasterPassword, setUnlockMasterPassword] = useState("");
  const [unlockConversationPassword, setUnlockConversationPassword] = useState("");
  const [unlockError, setUnlockError] = useState<string | null>(null);
  const [unlockNotice, setUnlockNotice] = useState<string | null>(null);
  const [isUnlockingConversation, setIsUnlockingConversation] = useState(false);
  const [messageDraft, setMessageDraft] = useState("");
  const [messageError, setMessageError] = useState<string | null>(null);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

  const selectedConversation =
    conversations.find((conversation) => conversation.id === selectedConversationId) ??
    conversations[0] ??
    null;
  const selectedAccessContext = selectedConversation
    ? conversationAccessContext[selectedConversation.id] ?? null
    : null;
  const selectedUnlockedConversation = selectedConversation
    ? getConversationKeyFromMemory(selectedConversation.id)
    : null;
  const selectedMessages = selectedConversation
    ? decryptedMessagesByConversation[selectedConversation.id] ?? []
    : [];
  const selectedRecipient = selectedConversation
    ? recipientInfoByConversation[selectedConversation.id] ?? null
    : null;
  const canComposeMessage = Boolean(selectedConversation && selectedUnlockedConversation && selectedRecipient && user);

  function upsertEncryptedMessages(records: PendingMessageRecord[]) {
    setEncryptedMessagesByConversation((currentMessages) => {
      const nextMessages = { ...currentMessages };

      for (const record of records) {
        const existingMessages = nextMessages[record.conversation_id] ?? [];
        if (existingMessages.some((message) => message.message_id === record.message_id)) {
          continue;
        }
        nextMessages[record.conversation_id] = [...existingMessages, record].sort((left, right) =>
          left.created_at.localeCompare(right.created_at),
        );
      }

      return nextMessages;
    });
  }

  function appendDecryptedMessage(nextMessage: ChatMessage) {
    setDecryptedMessagesByConversation((currentMessages) => {
      const existingMessages = currentMessages[nextMessage.conversationId] ?? [];
      if (existingMessages.some((message) => message.id === nextMessage.id)) {
        return currentMessages;
      }

      return {
        ...currentMessages,
        [nextMessage.conversationId]: [...existingMessages, nextMessage].sort((left, right) =>
          left.createdAt.localeCompare(right.createdAt),
        ),
      };
    });
  }

  function updateConversationActivity(conversationId: string, preview: string, updatedAt: string) {
    setConversations((currentConversations) =>
      currentConversations
        .map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                preview,
                updatedAt,
              }
            : conversation,
        )
        .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt)),
    );
  }

  async function decryptConversationMessages(conversationId: string, messageKey: CryptoKey) {
    if (!user) {
      return;
    }

    const encryptedMessages = encryptedMessagesByConversation[conversationId] ?? [];
    const nextDecryptedMessages: ChatMessage[] = [];

    for (const record of encryptedMessages) {
      try {
        const plaintext = await cryptoService.decryptMessage({
          payload: {
            encryption_type: record.encryption_type as EncryptionType,
            ciphertext: record.ciphertext,
            encrypted_message_key: record.encrypted_message_key,
            nonce: record.nonce,
            metadata: record.metadata,
          },
          messageKey,
        });

        nextDecryptedMessages.push({
          id: record.message_id,
          conversationId: record.conversation_id,
          text: plaintext,
          createdAt: record.created_at,
          direction: record.sender_id === user.user_id ? "outgoing" : "incoming",
          status: "sent",
          senderLabel: record.sender_id === user.user_id ? "You" : "Incoming",
        });
      } catch {
        setUnlockNotice("Some messages could not be opened with this password.");
      }
    }

    setDecryptedMessagesByConversation((currentMessages) => ({
      ...currentMessages,
      [conversationId]: nextDecryptedMessages,
    }));
  }

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
      setErrorMessage(error instanceof Error ? error.message : "Unable to load conversations right now.");
    } finally {
      setIsLoading(false);
    }
  }

  async function syncIncomingMessages(records: PendingMessageRecord[]) {
    if (!token) {
      return;
    }

    upsertEncryptedMessages(records);

    for (const record of records) {
      await messageService.acknowledgeMessage(token, {
        conversation_id: record.conversation_id,
        message_id: record.message_id,
        received_at: new Date().toISOString(),
      });

      const unlockedConversationKey = getConversationKeyFromMemory(record.conversation_id);
      if (unlockedConversationKey && user) {
        try {
          const plaintext = await cryptoService.decryptMessage({
            payload: {
              encryption_type: record.encryption_type as EncryptionType,
              ciphertext: record.ciphertext,
              encrypted_message_key: record.encrypted_message_key,
              nonce: record.nonce,
              metadata: record.metadata,
            },
            messageKey: unlockedConversationKey,
          });

          appendDecryptedMessage({
            id: record.message_id,
            conversationId: record.conversation_id,
            text: plaintext,
            createdAt: record.created_at,
            direction: record.sender_id === user.user_id ? "outgoing" : "incoming",
            status: "sent",
            senderLabel: record.sender_id === user.user_id ? "You" : "Incoming",
          });
          updateConversationActivity(record.conversation_id, plaintext, record.created_at);
        } catch {
          setUnlockNotice("A new message arrived. Open this chat to read it.");
        }
      }
    }
  }

  async function syncPendingMessages() {
    if (!token) {
      return;
    }

    try {
      const records = await messageService.fetchPendingMessages(token);
      if (records.length) {
        await syncIncomingMessages(records);
      }
    } catch (error) {
      setUnlockNotice(error instanceof Error ? error.message : "Unable to sync new messages right now.");
    }
  }

  useEffect(() => {
    void loadConversations();
  }, [token]);

  useEffect(() => {
    if (!token || !selectedConversation) {
      return;
    }

    let isCancelled = false;
    const authToken = token;
    const conversationId = selectedConversation.id;
    const conversationTitle = selectedConversation.title;
    const participantLabel = selectedConversation.participantLabel;

    async function loadConversationContext() {
      try {
        const [accessContext, encryptedMessages] = await Promise.all([
          conversationService.fetchConversationAccessContext(authToken, conversationId),
          messageService.listConversationMessages(authToken, conversationId),
        ]);

        if (isCancelled) {
          return;
        }

        setConversationAccessContext((currentContext) => ({
          ...currentContext,
          [conversationId]: accessContext,
        }));
        upsertEncryptedMessages(encryptedMessages);

        if (participantLabel === "Direct message") {
          const recipient = await messageService.fetchUserByUsername(conversationTitle, authToken);
          if (!isCancelled) {
            setRecipientInfoByConversation((currentRecipients) => ({
              ...currentRecipients,
              [conversationId]: {
                userId: recipient.user_id,
                username: recipient.username,
              },
            }));
          }
        }
      } catch (error) {
        if (!isCancelled) {
          setUnlockNotice(error instanceof Error ? error.message : "Unable to load this chat securely.");
        }
      }
    }

    void loadConversationContext();

    return () => {
      isCancelled = true;
    };
  }, [selectedConversation?.id, selectedConversation?.title, selectedConversation?.participantLabel, token]);

  useEffect(() => {
    if (!selectedConversation || !selectedUnlockedConversation) {
      return;
    }

    void decryptConversationMessages(selectedConversation.id, selectedUnlockedConversation);
  }, [selectedConversation?.id, selectedUnlockedConversation, encryptedMessagesByConversation]);

  useEffect(() => {
    if (!token) {
      return;
    }

    void syncPendingMessages();
    const interval = window.setInterval(() => {
      void syncPendingMessages();
    }, 8000);

    return () => {
      window.clearInterval(interval);
    };
  }, [token, unlockedConversationIds]);

  useEffect(() => {
    if (!token || !env.websocketUrl) {
      return;
    }

    const socket = new WebSocket(`${env.websocketUrl}?token=${encodeURIComponent(token)}`);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as
          | { action?: "deliver_message"; message?: PendingMessageRecord }
          | { action?: "pending_messages"; messages?: PendingMessageRecord[] };

        if (payload.action === "deliver_message" && payload.message) {
          void syncIncomingMessages([payload.message]);
        }

        if (payload.action === "pending_messages" && payload.messages) {
          void syncIncomingMessages(payload.messages);
        }
      } catch {
        return;
      }
    };

    return () => {
      socket.close();
    };
  }, [token, unlockedConversationIds, user?.user_id]);

  async function handleCreateConversation() {
    if (!token || !user) {
      return;
    }

    const normalizedUsername = targetUsername.trim();
    const sessionMasterPassword = getMasterPasswordFromMemory()?.trim() ?? "";
    const normalizedMasterPassword = createMasterPassword.trim() || sessionMasterPassword;
    const normalizedConversationPassword = createConversationPassword.trim();

    if (!normalizedUsername) {
      setCreateErrorMessage("Type a username to start a secure chat.");
      return;
    }

    if (!normalizedMasterPassword) {
      setCreateErrorMessage("Enter your master password to protect the conversation secret.");
      return;
    }

    if (!normalizedConversationPassword) {
      setCreateErrorMessage("Create a conversation password before starting the chat.");
      return;
    }

    if (normalizedConversationPassword !== confirmConversationPassword.trim()) {
      setCreateErrorMessage("Conversation passwords do not match.");
      return;
    }

    if (!user.encrypted_private_key || !user.private_key_wrap_salt || !user.private_key_wrap_kdf_params) {
      setCreateErrorMessage("This account is missing private-key protection metadata.");
      return;
    }

    if (!user.secret_wrap_salt || !user.secret_wrap_kdf_params) {
      setCreateErrorMessage("This account is missing secret-wrap metadata.");
      return;
    }

    setIsCreatingConversation(true);
    setCreateErrorMessage(null);
    setCreateSuccessMessage(null);

    try {
      await cryptoService.validateMasterPassword(
        user.encrypted_private_key,
        normalizedMasterPassword,
        user.private_key_wrap_salt,
        user.private_key_wrap_kdf_params,
      );

      const secretWrapKey = await cryptoService.deriveSecretWrapKey(
        normalizedMasterPassword,
        user.secret_wrap_salt,
        user.secret_wrap_kdf_params,
      );
      const conversationPasswordSaltB64 = toBase64(crypto.getRandomValues(new Uint8Array(16)));
      const messageKey = await cryptoService.deriveConversationMessageKey(
        normalizedConversationPassword,
        conversationPasswordSaltB64,
        CONVERSATION_KDF_PARAMS,
      );
      const unlockCheck = await cryptoService.createUnlockCheck(messageKey);
      const creatorAccess = await cryptoService.encryptConversationPassword(
        normalizedConversationPassword,
        secretWrapKey,
      );

      await conversationService.createConversation(token, {
        target_username: normalizedUsername,
        conversation_password_salt: conversationPasswordSaltB64,
        conversation_password_kdf_params: CONVERSATION_KDF_PARAMS,
        unlock_check_ciphertext: unlockCheck.ciphertext,
        unlock_check_nonce: unlockCheck.nonce,
        creator_access: creatorAccess,
      });

      setTargetUsername("");
      setCreateMasterPassword("");
      setCreateConversationPassword("");
      setConfirmConversationPassword("");
      setIsCreateChatOpen(false);
      rememberMasterPassword(normalizedMasterPassword);
      setCreateSuccessMessage("Chat created successfully.");
      await loadConversations();
    } catch (error) {
      setCreateErrorMessage(
        error instanceof Error ? error.message : "Unable to create the secure conversation.",
      );
    } finally {
      setIsCreatingConversation(false);
    }
  }

  async function handleUnlockConversation() {
    if (!selectedConversation || !selectedAccessContext || !user || !token) {
      return;
    }

    const sessionMasterPassword = getMasterPasswordFromMemory()?.trim() ?? "";
    const normalizedMasterPassword = unlockMasterPassword.trim() || sessionMasterPassword;
    const normalizedConversationPassword = unlockConversationPassword.trim();

    if (!normalizedMasterPassword) {
      setUnlockError("Enter your master password to unlock this chat.");
      return;
    }

    if (!normalizedConversationPassword) {
      setUnlockError("Enter the conversation password to read messages.");
      return;
    }

    if (!user.encrypted_private_key || !user.private_key_wrap_salt || !user.private_key_wrap_kdf_params) {
      setUnlockError("This account is missing private-key protection metadata.");
      return;
    }

    if (!user.secret_wrap_salt || !user.secret_wrap_kdf_params) {
      setUnlockError("This account is missing secret-wrap metadata.");
      return;
    }

    setIsUnlockingConversation(true);
    setUnlockError(null);
    setUnlockNotice(null);

    try {
      await cryptoService.validateMasterPassword(
        user.encrypted_private_key,
        normalizedMasterPassword,
        user.private_key_wrap_salt,
        user.private_key_wrap_kdf_params,
      );

      const secretWrapKey = await cryptoService.deriveSecretWrapKey(
        normalizedMasterPassword,
        user.secret_wrap_salt,
        user.secret_wrap_kdf_params,
      );

      if (selectedAccessContext.participant_access) {
        const decryptedStoredConversationPassword = await cryptoService.decryptConversationPassword(
          selectedAccessContext.participant_access.encrypted_conversation_password,
          selectedAccessContext.participant_access.nonce,
          secretWrapKey,
        );

        if (!cryptoService.constantTimeEqual(decryptedStoredConversationPassword, normalizedConversationPassword)) {
          throw new Error("Wrong conversation password.");
        }
      }

      const messageKey = await cryptoService.deriveConversationMessageKey(
        normalizedConversationPassword,
        selectedAccessContext.conversation_password_salt,
        selectedAccessContext.conversation_password_kdf_params,
      );
      const unlockIsValid = await cryptoService.verifyUnlockCheck(
        messageKey,
        selectedAccessContext.unlock_check_ciphertext,
        selectedAccessContext.unlock_check_nonce,
      );

      if (!unlockIsValid) {
        throw new Error("Wrong conversation password.");
      }

      if (!selectedAccessContext.has_stored_secret) {
        const wrappedConversationPassword = await cryptoService.encryptConversationPassword(
          normalizedConversationPassword,
          secretWrapKey,
        );
        await conversationService.saveConversationAccess(
          token,
          selectedConversation.id,
          wrappedConversationPassword,
        );
        setConversationAccessContext((currentContext) => ({
          ...currentContext,
          [selectedConversation.id]: {
            ...selectedAccessContext,
            participant_access: wrappedConversationPassword,
            has_stored_secret: true,
          },
        }));
      }

      rememberConversationKey(selectedConversation.id, messageKey);
      rememberMasterPassword(normalizedMasterPassword);
      setUnlockMasterPassword("");
      setUnlockConversationPassword("");
      setUnlockNotice("Chat opened successfully.");
    } catch (error) {
      setUnlockError(error instanceof Error ? error.message : "Unable to unlock this conversation.");
    } finally {
      setIsUnlockingConversation(false);
    }
  }

  async function handleSendMessage() {
    if (!token || !user || !selectedConversation || !selectedRecipient || !selectedUnlockedConversation) {
      return;
    }

    const normalizedMessage = messageDraft.trim();
    if (!normalizedMessage) {
      return;
    }

    setIsSendingMessage(true);
    setMessageError(null);

    try {
      const now = new Date().toISOString();
      const messageId = crypto.randomUUID();
      const encryptedPayload = await cryptoService.encryptMessage(EncryptionType.AES_GCM_CONVERSATION_V1, {
        plaintext: normalizedMessage,
        messageKey: selectedUnlockedConversation,
        encryptedMessageKey: "",
        metadata: {
          protected_by: "conversation_password",
        },
      });

      await messageService.sendMessage(token, {
        conversation_id: selectedConversation.id,
        sender_id: user.user_id,
        recipient_id: selectedRecipient.userId,
        encryption_type: encryptedPayload.encryption_type,
        ciphertext: encryptedPayload.ciphertext,
        encrypted_message_key: encryptedPayload.encrypted_message_key,
        nonce: encryptedPayload.nonce,
        message_id: messageId,
        created_at: now,
        metadata: encryptedPayload.metadata,
      });

      upsertEncryptedMessages([
        {
          conversation_id: selectedConversation.id,
          message_id: messageId,
          sender_id: user.user_id,
          recipient_id: selectedRecipient.userId,
          encryption_type: encryptedPayload.encryption_type,
          ciphertext: encryptedPayload.ciphertext,
          encrypted_message_key: encryptedPayload.encrypted_message_key,
          nonce: encryptedPayload.nonce,
          created_at: now,
          status: "DELIVERED",
          metadata: encryptedPayload.metadata,
        },
      ]);
      appendDecryptedMessage({
        id: messageId,
        conversationId: selectedConversation.id,
        text: normalizedMessage,
        createdAt: now,
        direction: "outgoing",
        status: "sent",
        senderLabel: "You",
      });
      updateConversationActivity(selectedConversation.id, normalizedMessage, now);
      setMessageDraft("");
    } catch (error) {
      setMessageError(error instanceof Error ? error.message : "Unable to send this message.");
    } finally {
      setIsSendingMessage(false);
    }
  }

  return (
    <main className="app-shell">
      <AppHeader onRefresh={() => void loadConversations()} onLogout={logout} />
      <section className="chat-layout">
        <aside className="conversation-sidebar">
          <div className="sidebar-search">
            <div className="sidebar-search-copy">
              <span className="eyebrow">New chat</span>
              <div className="sidebar-search-heading">
                <div>
                  <h2>Start a new conversation</h2>
                  <p className="sidebar-helper-text">Pick a username and set a password for this chat.</p>
                </div>
                <Button
                  type="button"
                  variant={isCreateChatOpen ? "secondary" : "primary"}
                  onClick={() => setIsCreateChatOpen((currentValue) => !currentValue)}
                >
                  {isCreateChatOpen ? "Close" : "Create chat"}
                </Button>
              </div>
            </div>
            {isCreateChatOpen ? (
              <div className="sidebar-search-form">
                <InputField
                  id="target-username"
                  label="Username"
                  placeholder="Type a username"
                  value={targetUsername}
                  onChange={(event) => setTargetUsername(event.target.value)}
                  autoComplete="off"
                  required
                />
                {!hasMasterPasswordInMemory ? (
                  <InputField
                    id="create-master-password"
                    label="Master password"
                    type="password"
                    placeholder="Enter your master password"
                    value={createMasterPassword}
                    onChange={(event) => setCreateMasterPassword(event.target.value)}
                    autoComplete="current-password"
                    required
                  />
                ) : null}
                <InputField
                  id="create-conversation-password"
                  label="Conversation password"
                  type="password"
                  placeholder="Create a password for this chat"
                  value={createConversationPassword}
                  onChange={(event) => setCreateConversationPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                />
                <InputField
                  id="confirm-conversation-password"
                  label="Confirm conversation password"
                  type="password"
                  placeholder="Repeat the conversation password"
                  value={confirmConversationPassword}
                  onChange={(event) => setConfirmConversationPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                />
                {createErrorMessage ? <div className="banner-error">{createErrorMessage}</div> : null}
                {createSuccessMessage ? <div className="banner-success">{createSuccessMessage}</div> : null}
                <Button
                  type="button"
                  variant="primary"
                  fullWidth
                  disabled={isCreatingConversation}
                  onClick={() => void handleCreateConversation()}
                >
                  {isCreatingConversation ? "Creating..." : "Create chat"}
                </Button>
              </div>
            ) : null}
          </div>
          <div className="sidebar-list">
            <div className="sidebar-list-header">
              <div className="sidebar-list-copy">
                <span className="eyebrow">Chats</span>
                <h2>Recent</h2>
              </div>
              <span className="sidebar-counter">{conversations.length}</span>
            </div>
            <ConversationList
              conversations={conversations}
              isLoading={isLoading}
              errorMessage={errorMessage}
              selectedConversationId={selectedConversation?.id ?? null}
              onSelectConversation={setSelectedConversationId}
            />
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
                  <div className="chat-identity-copy">
                    <h2>{selectedConversation.title}</h2>
                    <p className="muted">{selectedConversation.participantLabel}</p>
                  </div>
                </div>
                <div className="chat-security-badge">
                  {selectedUnlockedConversation ? "Open" : "Locked"}
                </div>
              </div>

              {selectedUnlockedConversation ? (
                <>
                  <div className="chat-timeline">
                    {selectedMessages.length ? (
                      selectedMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`message-row ${
                            message.direction === "outgoing" ? "message-row-outgoing" : ""
                          }`.trim()}
                        >
                          <div
                            className={`message-bubble ${
                              message.direction === "outgoing"
                                ? "message-bubble-sent"
                                : "message-bubble-received"
                            }`.trim()}
                          >
                            <p>{message.text}</p>
                            <span className="message-meta">
                              {message.senderLabel} at {formatTimestamp(message.createdAt)}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="chat-empty-inline">
                        <p>No messages yet.</p>
                      </div>
                    )}
                  </div>

                  <div className="chat-composer">
                    {unlockNotice ? <div className="banner-success">{unlockNotice}</div> : null}
                    {messageError ? <div className="banner-error">{messageError}</div> : null}
                    <div className="composer-shell">
                      <textarea
                        className="composer-input"
                        value={messageDraft}
                        onChange={(event) => setMessageDraft(event.target.value)}
                        placeholder="Write a message"
                        rows={3}
                      />
                      <Button
                        type="button"
                        variant="primary"
                        disabled={isSendingMessage || !messageDraft.trim() || !canComposeMessage}
                        onClick={() => void handleSendMessage()}
                      >
                        {isSendingMessage ? "Sending..." : "Send"}
                      </Button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="chat-locked-shell">
                <div className="chat-locked-card">
                  <span className="eyebrow">Unlock chat</span>
                    <h2>Enter this chat</h2>
                    <p className="muted">Use your passwords to open the conversation.</p>
                    <div className="chat-unlock-form">
                      {!hasMasterPasswordInMemory ? (
                        <InputField
                          id="unlock-master-password"
                          label="Master password"
                          type="password"
                          placeholder="Enter your master password"
                          value={unlockMasterPassword}
                          onChange={(event) => setUnlockMasterPassword(event.target.value)}
                          autoComplete="current-password"
                          required
                        />
                      ) : null}
                      <InputField
                        id="unlock-conversation-password"
                        label="Conversation password"
                        type="password"
                        placeholder="Enter the password for this chat"
                        value={unlockConversationPassword}
                        onChange={(event) => setUnlockConversationPassword(event.target.value)}
                        autoComplete="off"
                        required
                      />
                      {unlockError ? <div className="banner-error">{unlockError}</div> : null}
                      {unlockNotice ? <div className="banner-success">{unlockNotice}</div> : null}
                      <Button
                        type="button"
                        variant="primary"
                        disabled={isUnlockingConversation}
                        onClick={() => void handleUnlockConversation()}
                      >
                        {isUnlockingConversation ? "Opening..." : "Open chat"}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="panel-state chat-empty-state">
              <h2>Select a chat</h2>
              <p>Choose a conversation or start a new one.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
