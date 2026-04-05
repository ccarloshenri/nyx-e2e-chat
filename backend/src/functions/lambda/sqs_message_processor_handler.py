from src.functions.lambda.dependencies import get_message_controller
from src.utils.decorators import request_handler
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)


@request_handler
def handler(event, context):
    controller = get_message_controller()
    results = []
    for record in event.get("Records", []):
        results.append(controller.process_sqs_record(record))
    logger.info("sqs_batch_processed", extra={"context": {"records": len(results)}})
    return {"batchItemFailures": [], "results": results}
