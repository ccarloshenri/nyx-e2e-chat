import type { EncryptedMessagePayload } from "./encrypted_message_payload";

export type DecryptMessageInput = {
  payload: EncryptedMessagePayload;
  messageKey: CryptoKey;
};
