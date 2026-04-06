from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.controllers.auth_controller import AuthController
from src.layers.main.nyx.aws.aws_handler import aws_handler
from src.layers.main.nyx.aws.infrastructure.aws_infrastructure import AwsInfrastructure
from src.layers.main.nyx.interfaces.infrastructure.i_infrastructure import IInfrastructure
from src.layers.main.nyx.utils.logger import create_logger
from src.layers.main.nyx.services.jwt_token_service import JwtTokenService
from src.layers.main.nyx.services.password_hasher import PasswordHasher
from src.layers.main.nyx.services.system_clock import SystemClock
from src.layers.main.nyx.services.uuid_generator import UuidGenerator
from src.layers.main.nyx.validators.request_validator import RequestValidator

infrastructure: IInfrastructure = AwsInfrastructure()
logger = create_logger(__name__)
response_formatter = AwsResponseFormatter()
clock = SystemClock()
id_generator = UuidGenerator()
validator = RequestValidator()
password_hasher = PasswordHasher()
jwt_service = JwtTokenService(clock, id_generator)
user_dao = infrastructure.get_user_dao()
auth_bo = AuthBO(
    user_dao=user_dao,
    password_hasher=password_hasher,
    jwt_service=jwt_service,
    id_generator=id_generator,
    clock=clock,
)
controller = AuthController(
    auth_bo=auth_bo,
    validator=validator,
    logger=logger,
    response_formatter=response_formatter,
)


@aws_handler(logger, response_formatter)
def lambda_handler(event, context):
    return controller.register_user(event)
