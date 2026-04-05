from src.functions.lambda.dependencies import get_conversation_controller
from src.utils.decorators import request_handler


@request_handler
def handler(event, context):
    controller = get_conversation_controller()
    return controller.create_conversation(event)
