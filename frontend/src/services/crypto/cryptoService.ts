import {
  EncryptionStrategyFactory,
  type DecryptMessageInput,
  type EncryptMessageInput,
  type EncryptedMessagePayload,
  EncryptionType,
  MessageDecryptionService,
  MessageEncryptionService,
} from "../../crypto";
import { base64ToArrayBuffer } from "../../crypto/utils/base64";

const strategyFactory = EncryptionStrategyFactory.createDefault();
const messageEncryptionService = new MessageEncryptionService(strategyFactory);
const messageDecryptionService = new MessageDecryptionService(strategyFactory);
const DEFAULT_KDF_ITERATIONS = 310000;
const DEFAULT_SALT_BYTES = 16;
const AES_IV_BYTES = 12;
const UNLOCK_CHECK_VALUE = "nyx-conversation-unlock-check";

/**
 * Frontend-only crypto orchestration for authentication proofs, wrapped conversation
 * secrets, and end-to-end message encryption. Plaintext secrets are handled only
 * for the duration of the current operation and are never persisted by this service.
 */

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;

  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  return bytesToBase64(new Uint8Array(buffer));
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

function randomBytes(length: number): Uint8Array {
  return Uint8Array.from(crypto.getRandomValues(new Uint8Array(length)));
}

function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function readIterations(kdfParams: Record<string, unknown> | undefined): number {
  return Number(kdfParams?.iterations ?? DEFAULT_KDF_ITERATIONS);
}

async function digestBase64(buffer: BufferSource): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return arrayBufferToBase64(digest);
}

async function deriveBitsFromPassword(password: string, salt: Uint8Array, iterations: number) {
  const passwordKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );

  return crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: toArrayBuffer(salt),
      iterations,
      hash: "SHA-256",
    },
    passwordKey,
    256,
  );
}

async function deriveAesKeyFromPassword(password: string, salt: Uint8Array, iterations: number) {
  const passwordKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"],
  );

  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: toArrayBuffer(salt),
      iterations,
      hash: "SHA-256",
    },
    passwordKey,
    {
      name: "AES-GCM",
      length: 256,
    },
    false,
    ["encrypt", "decrypt"],
  );
}

async function generateKeyPair() {
  const keyPair = await crypto.subtle.generateKey(
    {
      name: "RSA-OAEP",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["encrypt", "decrypt"],
  );

  const exportedPublicKey = await crypto.subtle.exportKey("spki", keyPair.publicKey);
  const exportedPrivateKey = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

  return {
    publicKey: arrayBufferToBase64(exportedPublicKey),
    privateKey: exportedPrivateKey,
  };
}

async function importPrivateKey(privateKeyBuffer: ArrayBuffer): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "pkcs8",
    privateKeyBuffer,
    {
      name: "RSA-OAEP",
      hash: "SHA-256",
    },
    false,
    ["decrypt"],
  );
}

function parseEncryptedBlob(encryptedPayload: string): { iv: string; ciphertext: string } {
  return JSON.parse(encryptedPayload) as {
    iv: string;
    ciphertext: string;
  };
}

async function decryptPrivateKeyForValidation(
  encryptedPrivateKey: string,
  masterPassword: string,
  privateKeyWrapSalt: string,
  privateKeyWrapKdfParams: Record<string, unknown>,
): Promise<CryptoKey> {
  const parsedPrivateKey = parseEncryptedBlob(encryptedPrivateKey);
  const wrapKey = await deriveAesKeyFromPassword(
    masterPassword,
    base64ToBytes(privateKeyWrapSalt),
    readIterations(privateKeyWrapKdfParams),
  );
  const privateKeyBuffer = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: base64ToArrayBuffer(parsedPrivateKey.iv),
    },
    wrapKey,
    base64ToArrayBuffer(parsedPrivateKey.ciphertext),
  );
  return importPrivateKey(privateKeyBuffer);
}

async function buildAccountRegistration(masterPassword: string) {
  // The verifier authenticates the user without sending the plaintext master password.
  const authSalt = randomBytes(DEFAULT_SALT_BYTES);
  const secretWrapSalt = randomBytes(DEFAULT_SALT_BYTES);
  const privateKeyWrapSalt = randomBytes(DEFAULT_SALT_BYTES);
  const authKdfParams = {
    algorithm: "PBKDF2",
    iterations: DEFAULT_KDF_ITERATIONS,
    hash: "SHA-256",
  };
  const secretWrapKdfParams = {
    algorithm: "PBKDF2",
    iterations: DEFAULT_KDF_ITERATIONS,
    hash: "SHA-256",
    encryption: "AES-GCM",
    key_length: 256,
  };
  const privateKeyWrapKdfParams = {
    algorithm: "PBKDF2",
    iterations: DEFAULT_KDF_ITERATIONS,
    hash: "SHA-256",
    encryption: "AES-GCM",
    key_length: 256,
  };

  const authKeyBits = await deriveBitsFromPassword(masterPassword, authSalt, DEFAULT_KDF_ITERATIONS);
  const masterPasswordVerifier = await digestBase64(authKeyBits);
  const privateKeyWrapKey = await deriveAesKeyFromPassword(
    masterPassword,
    privateKeyWrapSalt,
    DEFAULT_KDF_ITERATIONS,
  );
  const { publicKey, privateKey } = await generateKeyPair();
  const privateKeyIv = randomBytes(AES_IV_BYTES);
  const encryptedPrivateKey = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: toArrayBuffer(privateKeyIv),
    },
    privateKeyWrapKey,
    privateKey,
  );

  return {
    master_password_verifier: masterPasswordVerifier,
    master_password_salt: bytesToBase64(authSalt),
    master_password_kdf_params: authKdfParams,
    secret_wrap_salt: bytesToBase64(secretWrapSalt),
    secret_wrap_kdf_params: secretWrapKdfParams,
    public_key: publicKey,
    encrypted_private_key: JSON.stringify({
      algorithm: "AES-GCM",
      iv: bytesToBase64(privateKeyIv),
      ciphertext: arrayBufferToBase64(encryptedPrivateKey),
    }),
    private_key_wrap_salt: bytesToBase64(privateKeyWrapSalt),
    private_key_wrap_kdf_params: privateKeyWrapKdfParams,
  };
}

function decodeJwtPayload(token: string): Record<string, unknown> {
  const [, payload] = token.split(".");
  if (!payload) {
    throw new Error("Invalid login challenge.");
  }
  const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  return JSON.parse(atob(padded)) as Record<string, unknown>;
}

async function createLoginProof(
  masterPassword: string,
  challengeToken: string,
  masterPasswordSalt: string,
  masterPasswordKdfParams: Record<string, unknown>,
): Promise<string> {
  // The proof signs the server nonce with material derived locally from the master password.
  const challengePayload = decodeJwtPayload(challengeToken);
  const nonce = String(challengePayload.nonce ?? "");
  if (!nonce) {
    throw new Error("Invalid login challenge.");
  }

  const authKeyBits = await deriveBitsFromPassword(
    masterPassword,
    base64ToBytes(masterPasswordSalt),
    readIterations(masterPasswordKdfParams),
  );
  const verifier = await digestBase64(authKeyBits);
  const signingKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(verifier),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    signingKey,
    toArrayBuffer(new TextEncoder().encode(nonce)),
  );
  return arrayBufferToBase64(signature);
}

async function deriveSecretWrapKey(
  masterPassword: string,
  secretWrapSalt: string,
  secretWrapKdfParams: Record<string, unknown>,
): Promise<CryptoKey> {
  return deriveAesKeyFromPassword(
    masterPassword,
    base64ToBytes(secretWrapSalt),
    readIterations(secretWrapKdfParams),
  );
}

async function encryptConversationPassword(
  conversationPassword: string,
  secretWrapKey: CryptoKey,
): Promise<{ encrypted_conversation_password: string; nonce: string }> {
  const iv = randomBytes(AES_IV_BYTES);
  const ciphertext = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: toArrayBuffer(iv),
    },
    secretWrapKey,
    new TextEncoder().encode(conversationPassword),
  );

  return {
    encrypted_conversation_password: arrayBufferToBase64(ciphertext),
    nonce: bytesToBase64(iv),
  };
}

async function decryptConversationPassword(
  encryptedConversationPassword: string,
  nonce: string,
  secretWrapKey: CryptoKey,
): Promise<string> {
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: base64ToArrayBuffer(nonce),
    },
    secretWrapKey,
    base64ToArrayBuffer(encryptedConversationPassword),
  );

  return new TextDecoder().decode(plaintext);
}

async function deriveConversationMessageKey(
  conversationPassword: string,
  conversationPasswordSalt: string,
  conversationPasswordKdfParams: Record<string, unknown>,
): Promise<CryptoKey> {
  return deriveAesKeyFromPassword(
    conversationPassword,
    base64ToBytes(conversationPasswordSalt),
    readIterations(conversationPasswordKdfParams),
  );
}

async function createUnlockCheck(messageKey: CryptoKey): Promise<{ ciphertext: string; nonce: string }> {
  // This encrypted constant lets the client verify the conversation password locally.
  const iv = randomBytes(AES_IV_BYTES);
  const ciphertext = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: toArrayBuffer(iv),
    },
    messageKey,
    new TextEncoder().encode(UNLOCK_CHECK_VALUE),
  );

  return {
    ciphertext: arrayBufferToBase64(ciphertext),
    nonce: bytesToBase64(iv),
  };
}

async function verifyUnlockCheck(
  messageKey: CryptoKey,
  unlockCheckCiphertext: string,
  unlockCheckNonce: string,
): Promise<boolean> {
  try {
    const plaintext = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: base64ToArrayBuffer(unlockCheckNonce),
      },
      messageKey,
      base64ToArrayBuffer(unlockCheckCiphertext),
    );
    return new TextDecoder().decode(plaintext) === UNLOCK_CHECK_VALUE;
  } catch {
    return false;
  }
}

function constantTimeEqual(left: string, right: string): boolean {
  // Avoid short-circuit string comparison when checking local secret equality.
  const leftBytes = new TextEncoder().encode(left);
  const rightBytes = new TextEncoder().encode(right);
  if (leftBytes.length !== rightBytes.length) {
    return false;
  }

  let mismatch = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    mismatch |= leftBytes[index] ^ rightBytes[index];
  }

  return mismatch === 0;
}

export function createCryptoService() {
  return {
    async buildAccountRegistration(masterPassword: string) {
      return buildAccountRegistration(masterPassword);
    },
    async createLoginProof(
      masterPassword: string,
      challengeToken: string,
      masterPasswordSalt: string,
      masterPasswordKdfParams: Record<string, unknown>,
    ) {
      return createLoginProof(
        masterPassword,
        challengeToken,
        masterPasswordSalt,
        masterPasswordKdfParams,
      );
    },
    async validateMasterPassword(
      encryptedPrivateKey: string,
      masterPassword: string,
      privateKeyWrapSalt: string,
      privateKeyWrapKdfParams: Record<string, unknown>,
    ) {
      return decryptPrivateKeyForValidation(
        encryptedPrivateKey,
        masterPassword,
        privateKeyWrapSalt,
        privateKeyWrapKdfParams,
      );
    },
    async deriveSecretWrapKey(
      masterPassword: string,
      secretWrapSalt: string,
      secretWrapKdfParams: Record<string, unknown>,
    ) {
      return deriveSecretWrapKey(masterPassword, secretWrapSalt, secretWrapKdfParams);
    },
    async encryptConversationPassword(
      conversationPassword: string,
      secretWrapKey: CryptoKey,
    ) {
      return encryptConversationPassword(conversationPassword, secretWrapKey);
    },
    async decryptConversationPassword(
      encryptedConversationPassword: string,
      nonce: string,
      secretWrapKey: CryptoKey,
    ) {
      return decryptConversationPassword(encryptedConversationPassword, nonce, secretWrapKey);
    },
    async deriveConversationMessageKey(
      conversationPassword: string,
      conversationPasswordSalt: string,
      conversationPasswordKdfParams: Record<string, unknown>,
    ) {
      return deriveConversationMessageKey(
        conversationPassword,
        conversationPasswordSalt,
        conversationPasswordKdfParams,
      );
    },
    async createUnlockCheck(messageKey: CryptoKey) {
      return createUnlockCheck(messageKey);
    },
    async verifyUnlockCheck(
      messageKey: CryptoKey,
      unlockCheckCiphertext: string,
      unlockCheckNonce: string,
    ) {
      return verifyUnlockCheck(messageKey, unlockCheckCiphertext, unlockCheckNonce);
    },
    constantTimeEqual,
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
