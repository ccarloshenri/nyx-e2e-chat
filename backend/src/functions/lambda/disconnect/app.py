from src.layers.main.nyx.bootstrap.container import build_websocket_controller
from src.layers.main.nyx.decorators.handler import handler

controller = build_websocket_controller()


@handler
def lambda_handler(event, context):
    return controller.disconnect(event)
