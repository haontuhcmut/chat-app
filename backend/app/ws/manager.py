from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, key: str, ws: WebSocket):
        await ws.accept()
        self.connections[key].add(ws)

    async def disconnect(self, key: str, ws: WebSocket):
        self.connections[key].discard(ws)
        if not self.connections[key]:
            del self.connections[key]

    async def send(self, key: str, data: dict):
        for ws in list(self.connections.get(key, [])):
            await ws.send_json(data)

