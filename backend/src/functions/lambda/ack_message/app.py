from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.controllers.message_controller import MessageController
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
message_bo = MessageBO(
    infrastructure=infrastructure,
)
controller = MessageController(
    message_bo=message_bo,
    validator=validator,
    jwt_service=jwt_service,
    logger=logger,
)


@handler(logger)
def lambda_handler(event, context):
    return controller.ack_message(event)
