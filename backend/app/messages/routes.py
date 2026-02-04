from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Depends
from typing import Annotated

from .schema import CreateMessage
from ..auth.dependency import AccessTokenBearer
from ..friends.deps import friendship_service
from ..friends.services import FriendshipService
from ..messages.services import MessageService
from ..core.dependency import SessionDep

message_router = APIRouter()
message_services = MessageService()


@message_router.post("/direct")
async def direct_message(
    data: CreateMessage,
    access_token: Annotated[dict, Depends(AccessTokenBearer())],
    friendship: Annotated[FriendshipService, Depends(friendship_service)],
    session: SessionDep,
):
    new_message = await message_services.send_direct_message(
        data, UUID(access_token["user_id"]), friendship, session
    )
    return new_message
