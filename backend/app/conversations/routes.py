from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from .schema import CreateConvRequest, MessageResponse, ConversationResponse
from ..core.dependency import SessionDep
from ..auth.dependency import AccessTokenBearer
from .services import ConvServices
from fastapi_pagination import Params, Page

from ..deps.require_friends import require_friendships

conv_services = ConvServices()
conv_router = APIRouter()
@conv_router.post("/", dependencies=[Depends(require_friendships)])
async def create_conversation(data: CreateConvRequest, session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    conv = await  conv_services.create_conv(UUID(access_token["user_id"]), data, session)
    return conv

@conv_router.get("/", response_model=Page[ConversationResponse])
async def get_conversations(session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())], _params: Annotated[Params, Depends()]):
    convs = await conv_services.get_all_conv(UUID(access_token["user_id"]), session)
    return convs

@conv_router.get("/messages", response_model=Page[MessageResponse])
async def get_messages(conv_id: UUID, session: SessionDep, _access_token: Annotated[dict, Depends(AccessTokenBearer())], _params: Annotated[Params, Depends()]):
    messages = await conv_services.get_messages(conv_id, session)
    return messages
