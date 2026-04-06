from src.layers.main.nyx.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.controllers.websocket_controller import WebSocketController
from src.layers.main.nyx.decorators.handler import handler
from src.layers.main.nyx.infrastructure.aws_infrastructure import AwsInfrastructure
from src.layers.main.nyx.interfaces.infrastructure.i_infrastructure import IInfrastructure
from src.layers.main.nyx.utils.logger import create_logger
from src.layers.main.nyx.services.jwt_token_service import JwtTokenService
from src.layers.main.nyx.services.system_clock import SystemClock
from src.layers.main.nyx.services.uuid_generator import UuidGenerator
from src.layers.main.nyx.validators.request_validator import RequestValidator

infrastructure: IInfrastructure = AwsInfrastructure()
logger = create_logger(__name__)
clock = SystemClock()
id_generator = UuidGenerator()
validator = RequestValidator()
jwt_service = JwtTokenService(clock, id_generator)
connection_dao = infrastructure.get_connection_dao()
connection_bo = ConnectionBO(connection_dao=connection_dao, clock=clock)
controller = WebSocketController(
    connection_bo=connection_bo,
    validator=validator,
    jwt_service=jwt_service,
    logger=logger,
)


@handler(logger)
def lambda_handler(event, context):
    return controller.disconnect(event)
