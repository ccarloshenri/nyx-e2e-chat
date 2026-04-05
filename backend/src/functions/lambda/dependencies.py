from src.layers.main.nyx.bootstrap.container import get_container


def get_auth_controller():
    return get_container().get_auth_controller()


def get_websocket_controller():
    return get_container().get_websocket_controller()


def get_message_controller():
    return get_container().get_message_controller()


def get_conversation_controller():
    return get_container().get_conversation_controller()
