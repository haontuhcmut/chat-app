from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from .schema import CreateConvRequest
from ..core.dependency import SessionDep
from ..auth.dependency import AccessTokenBearer
from .services import ConvServices

conv_services = ConvServices()
conv_router = APIRouter()
@conv_router.post("/")
async def create_conversation(data: CreateConvRequest, session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    conv = await  conv_services.create_conv(UUID(access_token["user_id"]), data, session)
    return conv

@conv_router.get("/")
async def get_conversations(session: SessionDep, access_token: Annotated[dict, Depends(AccessTokenBearer())]):
    convs = await conv_services.get_all_conv(UUID(access_token["user_id"]), session)
    return convs