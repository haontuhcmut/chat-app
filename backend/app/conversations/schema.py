from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
import enum

class APIModel(BaseModel):
    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }

class ConvType(str, enum.Enum):
    direct = "direct"
    group = "group"


class CreateConvRequest(BaseModel):
    type: ConvType
    name: str | None = None
    member_id: list[UUID]

class MessageResponse(APIModel):
    id: UUID = Field(alias="_id")
    conv_id: UUID = Field(alias="conversationId")
    sender_user_id: UUID = Field(alias="senderId")
    content: str | None
    img_url: str | None = Field(default=None, alias="imgUrl")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    created_at: datetime = Field(alias="createdAt")

class UserConvResponse(BaseModel):
    conv_id: UUID

class ParticipantResponse(APIModel):
    id: UUID = Field(alias="_id")
    displayName: str | None
    avatarUrl: str | None
    joinedAt: datetime

class SeenUserResponse(APIModel):
    id: UUID = Field(alias="_id")
    displayName: str | None
    avatarUrl: str | None


class GroupResponse(APIModel):
    name: str
    createdBy: UUID


class LastMessageSender(APIModel):
    id: UUID = Field(alias="_id")
    displayName: str
    avatarUrl: str | None = None


class LastMessageResponse(APIModel):
    id: UUID = Field(alias="_id")
    content: str
    createdAt: datetime
    sender: LastMessageSender


class ConversationResponseItem(APIModel):
    id: UUID = Field(alias="_id")
    type: str
    group: GroupResponse | None
    participants: list[ParticipantResponse]
    lastMessageAt: datetime | None
    seenBy: list[SeenUserResponse]
    lastMessage: LastMessageResponse | None
    unreadCounts: dict[str, int]
    createdAt: datetime
    updatedAt: datetime


class ConversationResponse(BaseModel):
    conversations: list[ConversationResponseItem]
