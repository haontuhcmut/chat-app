import uuid


class RedisConnectionStore:
    def __init__(self, redis):
        self. redis = redis

    def _key(self, client_id: str):
        return f"ws:user:{client_id}"

    async def add_connection(self, client_id: str) -> str:
        conn_id = str(uuid.uuid4())

        await self.redis.sadd(self._key(client_id), conn_id)
        return conn_id

    async def remove_connection(self, client_id: str, conn_id: str):
        await self.redis.srem(self._key(client_id), conn_id)

    async def count(self, client_id: str) -> int:
        return await self.redis.scard(self._key(client_id))

    async def is_online(self, client_id: str) -> bool:
        return (await self.count(client_id)) > 0
    
