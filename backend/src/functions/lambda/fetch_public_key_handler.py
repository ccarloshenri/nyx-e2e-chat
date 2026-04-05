from src.functions.lambda.dependencies import get_auth_controller
from src.utils.decorators import request_handler


@request_handler
def handler(event, context):
    controller = get_auth_controller()
    return controller.fetch_public_key(event)
