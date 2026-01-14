import redis.asyncio as aioredis

from ..config import Config

token_blocklist = aioredis.from_url(Config.BACKEND_URL)
async def add_jti_blocklist(jti: str) -> None:
    await token_blocklist.set(name=jti, value="", ex=3600*24*7)

async def token_in_jti_blocklist(jti: str) -> bool:
    jti = await token_blocklist.get(name=jti)
    return jti is not None
