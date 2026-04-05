import type { DecryptMessageInput } from "../types/decrypt_message_input";
import type { EncryptMessageInput } from "../types/encrypt_message_input";
import type { EncryptedMessagePayload } from "../types/encrypted_message_payload";
import type { EncryptionType } from "../types/encryption_type";

export interface IEncryptionStrategy {
  getEncryptionType(): EncryptionType;
  encrypt(input: EncryptMessageInput): Promise<EncryptedMessagePayload>;
  decrypt(input: DecryptMessageInput): Promise<string>;
}
