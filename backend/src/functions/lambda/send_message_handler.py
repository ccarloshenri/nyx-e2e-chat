from src.functions.lambda.dependencies import get_message_controller
from src.utils.decorators import request_handler


@request_handler
def handler(event, context):
    controller = get_message_controller()
    return controller.send_message(event)
