from uuid import UUID

from pydantic import BaseModel

class AddFriendSchema(BaseModel):
    to_user_id: UUID
    message: str | None = None
