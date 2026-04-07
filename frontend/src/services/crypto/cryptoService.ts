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
const REGISTRATION_KDF_ITERATIONS = 250000;
const REGISTRATION_KDF_SALT_BYTES = 16;
const REGISTRATION_AES_IV_BYTES = 12;

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

async function deriveKeyFromPassword(password: string, salt: Uint8Array, iterations: number) {
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

async function buildRegistrationKeyMaterial(password: string) {
  const { publicKey, privateKey } = await generateKeyPair();
  const salt = randomBytes(REGISTRATION_KDF_SALT_BYTES);
  const iv = randomBytes(REGISTRATION_AES_IV_BYTES);
  const encryptionKey = await deriveKeyFromPassword(password, salt, REGISTRATION_KDF_ITERATIONS);
  const encryptedPrivateKey = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: toArrayBuffer(iv),
    },
    encryptionKey,
    privateKey,
  );

  return {
    public_key: publicKey,
    encrypted_private_key: JSON.stringify({
      algorithm: "AES-GCM",
      iv: bytesToBase64(iv),
      ciphertext: arrayBufferToBase64(encryptedPrivateKey),
    }),
    kdf_salt: bytesToBase64(salt),
    kdf_params: {
      algorithm: "PBKDF2",
      iterations: REGISTRATION_KDF_ITERATIONS,
      hash: "SHA-256",
      encryption: "AES-GCM",
      key_length: 256,
    },
  };
}

export function createCryptoService() {
  return {
    async generateKeyPair() {
      return generateKeyPair();
    },
    async deriveKeyFromPassword(password: string, salt: Uint8Array, iterations = REGISTRATION_KDF_ITERATIONS) {
      return deriveKeyFromPassword(password, salt, iterations);
    },
    async buildRegistrationKeyMaterial(password: string) {
      return buildRegistrationKeyMaterial(password);
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
