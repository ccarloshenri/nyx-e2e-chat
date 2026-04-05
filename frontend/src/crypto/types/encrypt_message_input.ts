import type { EncryptedMessageMetadata } from "./encrypted_message_metadata";

export type EncryptMessageInput = {
  plaintext: string;
  messageKey: CryptoKey;
  encryptedMessageKey: string;
  metadata?: EncryptedMessageMetadata;
};
