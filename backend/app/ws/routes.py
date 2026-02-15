import secrets
from typing import Annotated
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from ..auth.dependency import AccessTokenBearer
from ..core.redis import redis_client


ws_router = APIRouter()
@ws_router.get("/")
async def get_session_id(access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    # Create session.id
    sid = secrets.token_urlsafe(32)

    await redis_client.setex(
        name=f"ws_session:{sid}",
        time=300, # 5 mins
        value=access_token.get("user_id")
    )
    return JSONResponse(status_code=200, content={"sid": sid})