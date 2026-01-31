from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
import enum


class ConvType(str, enum.Enum):
    direct = "direct"
    group = "group"


class CreateConvRequest(BaseModel):
    type: ConvType
    name: str | None = None
    member_id: list[UUID]

class ParticipantResponse(BaseModel):
    user_id: UUID
    username: str
    avatar_url: str | None
    joined_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    type: ConvType
    last_message_content: str | None
    last_message_at: datetime | None
    unread_count: int
    participants: list[ParticipantResponse]

class MessageResponse(BaseModel):
    id: UUID
    sender_user_id: UUID
    content: str
    img_url: str | None
    created_at: datetime
    updated_at: datetime
