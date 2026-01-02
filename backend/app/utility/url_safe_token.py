import logging
from itsdangerous import URLSafeSerializer
from ..config import Config

#Create url-token-safe
serialize = URLSafeSerializer(
    secret_key=Config.SECRET_KEY,
    salt=Config.SALT,
)

def encode_url_safe_token(data: dict) -> str:
    token = serialize.dumps(data)
    return token

def decode_url_safe_token(token: str):
    try:
        data = serialize.loads(token)
        return data
    except Exception as e:
        logging.error(str(e))
