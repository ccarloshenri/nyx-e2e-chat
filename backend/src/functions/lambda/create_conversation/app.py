from src.layers.main.nyx.bootstrap.container import build_conversation_controller
from src.layers.main.nyx.decorators.handler import handler

controller = build_conversation_controller()


@handler
def lambda_handler(event, context):
    return controller.create_conversation(event)
