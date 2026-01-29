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

