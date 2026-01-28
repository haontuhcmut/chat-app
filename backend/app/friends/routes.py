from typing import Annotated

from fastapi import APIRouter, Depends
from .schema import AddFriendSchema
from .services import FriendServices
from ..core.dependency import SessionDep
from ..auth.dependency import AccessTokenBearer
from uuid import UUID

friend_service = FriendServices()

friend_router = APIRouter()


@friend_router.post("/requests")
async def requests(
    data_request: AddFriendSchema,
    session: SessionDep,
    access_token: Annotated[dict, Depends(AccessTokenBearer())],
):
    new_request = await friend_service.add_friend(
        UUID(access_token.get("user_id")), data_request, session
    )
    return new_request


@friend_router.post("/requests/{request_id}/accept")
async def accept_friend(
    request_id: str,
    session: SessionDep,
    access_token: Annotated[dict, Depends(AccessTokenBearer())],
):
    accept_request = await friend_service.accept_request_friend(
        UUID(access_token.get("user_id")), request_id, session
    )
    return accept_request

@friend_router.delete("/requests/{request_id}/decline", status_code=204)
async def decline_friend(request_id:str, session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    decline_request = await friend_service.decline_request_friend(UUID(access_token.get("user_id")), request_id, session)
    return decline_request

@friend_router.get("/")
async def all_friends(session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    friends = await friend_service.get_all_friends(UUID(access_token.get("user_id")), session)
    return friends

@friend_router.get("/requests")
async def sent_received_requests(session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    results = await friend_service.get_friend_requests(UUID(access_token.get("user_id")), session)
    return results
