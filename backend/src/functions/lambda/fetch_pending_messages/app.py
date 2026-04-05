from src.layers.main.nyx.bootstrap.container import build_message_controller
from src.layers.main.nyx.decorators.handler import handler

controller = build_message_controller()


@handler
def lambda_handler(event, context):
    return controller.fetch_pending_messages(event)
