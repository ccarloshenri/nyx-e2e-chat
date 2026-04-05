from src.functions.lambda.dependencies import get_websocket_controller
from src.utils.decorators import request_handler


@request_handler
def handler(event, context):
    controller = get_websocket_controller()
    return controller.disconnect(event)
