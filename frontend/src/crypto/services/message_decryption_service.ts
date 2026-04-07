import { EncryptionStrategyFactory } from "../factories/encryption_strategy_factory";
import type { DecryptMessageInput } from "../types/decrypt_message_input";

export class MessageDecryptionService {
  constructor(private readonly strategyFactory: EncryptionStrategyFactory) {}

  async decrypt(input: DecryptMessageInput): Promise<string> {
    const strategy = this.strategyFactory.getStrategy(input.payload.encryption_type);

    return strategy.decrypt(input);
  }
}
