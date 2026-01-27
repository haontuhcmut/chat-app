from typing import Annotated

from fastapi import APIRouter, Depends
from .schema import AddFriendSchema
from .services import FriendServices
from ..auth.schema import UserModel
from ..core.dependency import SessionDep
from ..auth.dependency import get_current_user, AccessTokenBearer

friend_service = FriendServices()

friend_router = APIRouter()


@friend_router.post("/requests")
async def requests(
    current_me: Annotated[UserModel, Depends(get_current_user)],
    data_request: AddFriendSchema,
    session: SessionDep,
    _access_token: Annotated[dict, Depends(AccessTokenBearer())],
):
    new_request = await friend_service.add_friend(current_me, data_request, session)
    return new_request

