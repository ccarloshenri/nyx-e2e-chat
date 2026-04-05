import type { IEncryptionStrategy } from "../interfaces/encryption_strategy";
import type { EncryptionType } from "../types/encryption_type";

export class EncryptionStrategyRegistry {
  private readonly strategies = new Map<EncryptionType, IEncryptionStrategy>();

  register(strategy: IEncryptionStrategy): void {
    this.strategies.set(strategy.getEncryptionType(), strategy);
  }

  get(encryptionType: EncryptionType): IEncryptionStrategy {
    const strategy = this.strategies.get(encryptionType);

    if (!strategy) {
      throw new Error(`No encryption strategy registered for ${encryptionType}.`);
    }

    return strategy;
  }
}
