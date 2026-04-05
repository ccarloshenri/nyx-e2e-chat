from src.layers.main.nyx.bootstrap.container import build_auth_controller
from src.layers.main.nyx.decorators.handler import handler

controller = build_auth_controller()


@handler
def lambda_handler(event, context):
    return controller.register_user(event)
