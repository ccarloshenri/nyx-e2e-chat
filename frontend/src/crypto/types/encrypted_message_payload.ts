import type { EncryptedMessageMetadata } from "./encrypted_message_metadata";
import type { EncryptionType } from "./encryption_type";

export type EncryptedMessagePayload = {
  encryption_type: EncryptionType;
  ciphertext: string;
  encrypted_message_key: string;
  nonce: string;
  metadata?: EncryptedMessageMetadata;
};
