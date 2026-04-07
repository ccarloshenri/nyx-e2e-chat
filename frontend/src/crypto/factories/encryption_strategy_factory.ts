import type { IEncryptionStrategy } from "../interfaces/encryption_strategy";
import { EncryptionStrategyRegistry } from "../registry/encryption_strategy_registry";
import { AesGcmConversationV1EncryptionStrategy } from "../strategies/aes_gcm_conversation_v1_encryption_strategy";
import { AesGcmV1EncryptionStrategy } from "../strategies/aes_gcm_v1_encryption_strategy";
import type { EncryptionType } from "../types/encryption_type";

export class EncryptionStrategyFactory {
  constructor(private readonly registry: EncryptionStrategyRegistry) {}

  static createDefault(): EncryptionStrategyFactory {
    const registry = new EncryptionStrategyRegistry();

    registry.register(new AesGcmV1EncryptionStrategy());
    registry.register(new AesGcmConversationV1EncryptionStrategy());

    return new EncryptionStrategyFactory(registry);
  }

  getStrategy(encryptionType: EncryptionType): IEncryptionStrategy {
    return this.registry.get(encryptionType);
  }
}
