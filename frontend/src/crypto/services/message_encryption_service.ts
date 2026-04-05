import { EncryptionStrategyFactory } from "../factories/encryption_strategy_factory";
import type { EncryptMessageInput } from "../types/encrypt_message_input";
import type { EncryptedMessagePayload } from "../types/encrypted_message_payload";
import type { EncryptionType } from "../types/encryption_type";

export class MessageEncryptionService {
  constructor(private readonly strategyFactory: EncryptionStrategyFactory) {}

  async encrypt(
    encryptionType: EncryptionType,
    input: EncryptMessageInput,
  ): Promise<EncryptedMessagePayload> {
    const strategy = this.strategyFactory.getStrategy(encryptionType);

    return strategy.encrypt(input);
  }
}
