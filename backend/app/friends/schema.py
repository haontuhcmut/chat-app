from uuid import UUID

from pydantic import BaseModel

class AddFriendSchema(BaseModel):
    to_user_id: UUID
    message: str | None = None


class NewFriendResponse(BaseModel):
    from_user_id: UUID
    user_name: str
    avatar_url: str | None

class AllFriendsResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    avatar_url: str | None

class AllFriendsRequest(AllFriendsResponse):
    pass

class SentReceivedFriendsRequest(BaseModel):
    sent: list[AllFriendsRequest]
    received: list[AllFriendsResponse]