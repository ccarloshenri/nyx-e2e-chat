import {
  EncryptionStrategyFactory,
  type DecryptMessageInput,
  type EncryptMessageInput,
  type EncryptedMessagePayload,
  EncryptionType,
  MessageDecryptionService,
  MessageEncryptionService,
} from "../../crypto";

const strategyFactory = EncryptionStrategyFactory.createDefault();
const messageEncryptionService = new MessageEncryptionService(strategyFactory);
const messageDecryptionService = new MessageDecryptionService(strategyFactory);

async function generateMessageKey(): Promise<CryptoKey> {
  return crypto.subtle.generateKey(
    {
      name: "AES-GCM",
      length: 256,
    },
    true,
    ["encrypt", "decrypt"],
  );
}

export function createCryptoService() {
  return {
    async generateKeyPair() {
      throw new Error("Client-side asymmetric key generation is not implemented yet.");
    },
    async deriveKeyFromPassword() {
      throw new Error("Password-based key derivation is not implemented yet.");
    },
    async generateMessageKey() {
      return generateMessageKey();
    },
    async encryptMessage(
      encryptionType: EncryptionType,
      input: EncryptMessageInput,
    ): Promise<EncryptedMessagePayload> {
      return messageEncryptionService.encrypt(encryptionType, input);
    },
    async decryptMessage(input: DecryptMessageInput): Promise<string> {
      return messageDecryptionService.decrypt(input);
    },
  };
}
