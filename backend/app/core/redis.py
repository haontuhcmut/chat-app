import redis.asyncio as aioredis
import logging
from ..config import Config

logger = logging.getLogger(__name__)


token_blocklist = aioredis.from_url(Config.BACKEND_URL)
async def add_jti_blocklist(jti: str) -> None:
    try:
        await token_blocklist.set(name=jti, value="", ex=3600)
        logging.info(f"JTI added to redis: {jti}")
    except Exception:
        logger.error(f"Redis error while adding JTI")

async def token_in_jti_blocklist(jti: str) -> bool:
    jti = await token_blocklist.get(name=jti)
    return jti is not None

redis_client = aioredis.from_url(Config.BACKEND_URL)
