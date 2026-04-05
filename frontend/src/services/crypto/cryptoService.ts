export function createCryptoStub() {
  return {
    async generateKeyPair() {
      throw new Error("Client-side cryptography is not implemented yet.");
    },
    async deriveKeyFromPassword() {
      throw new Error("Password-based key derivation is not implemented yet.");
    },
    async encryptMessage() {
      throw new Error("Local message encryption is not implemented yet.");
    },
    async decryptMessage() {
      throw new Error("Local message decryption is not implemented yet.");
    }
  };
}
