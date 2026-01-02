from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from ..config import Config

# Config connection
mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_FROM_NAME="Customer services",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

mail = FastMail(config=mail_config)


def create_message(recipient: list[str], subject: str, body: str):
    message = MessageSchema(
        subject=subject, recipients=recipient, body=body, subtype=MessageType.html
    )

    return message
