from ..friends.services import FriendshipService

async def friendship_service() -> FriendshipService:
    return FriendshipService()
