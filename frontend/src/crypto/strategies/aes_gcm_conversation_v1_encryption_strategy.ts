import type { IEncryptionStrategy } from "../interfaces/encryption_strategy";
import type { DecryptMessageInput } from "../types/decrypt_message_input";
import type { EncryptMessageInput } from "../types/encrypt_message_input";
import type { EncryptedMessagePayload } from "../types/encrypted_message_payload";
import { EncryptionType } from "../types/encryption_type";
import { arrayBufferToBase64, base64ToArrayBuffer } from "../utils/base64";

const AES_GCM_NONCE_LENGTH = 12;

export class AesGcmConversationV1EncryptionStrategy implements IEncryptionStrategy {
  getEncryptionType(): EncryptionType {
    return EncryptionType.AES_GCM_CONVERSATION_V1;
  }

  async encrypt(input: EncryptMessageInput): Promise<EncryptedMessagePayload> {
    const nonce = crypto.getRandomValues(new Uint8Array(AES_GCM_NONCE_LENGTH));
    const encodedPlaintext = new TextEncoder().encode(input.plaintext);
    const ciphertextBuffer = await crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv: nonce,
      },
      input.messageKey,
      encodedPlaintext,
    );

    return {
      encryption_type: this.getEncryptionType(),
      ciphertext: arrayBufferToBase64(ciphertextBuffer),
      encrypted_message_key: "",
      nonce: arrayBufferToBase64(nonce.buffer),
      metadata: {
        ...input.metadata,
        version: 1,
        key_source: "conversation_password",
      },
    };
  }

  async decrypt(input: DecryptMessageInput): Promise<string> {
    if (input.payload.encryption_type !== this.getEncryptionType()) {
      throw new Error("AES_GCM_CONVERSATION_V1 strategy cannot decrypt a different encryption type.");
    }

    const ciphertext = base64ToArrayBuffer(input.payload.ciphertext);
    const nonce = base64ToArrayBuffer(input.payload.nonce);
    const plaintextBuffer = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: nonce,
      },
      input.messageKey,
      ciphertext,
    );

    return new TextDecoder().decode(plaintextBuffer);
  }
}
