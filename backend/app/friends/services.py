from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
from fastapi.responses import JSONResponse

from ..core.model import User, FriendRequests, Friend

from ..auth.schema import UserModel
from ..friends.schema import AddFriendSchema
import logging

logger = logging.getLogger(__name__)


class FriendServices:
    async def add_friend(
        self,
        current_me: UserModel,
        data_request: AddFriendSchema,
        session: AsyncSession,
    ):

        data = data_request.model_dump()
        if data_request.to_user_id == current_me.id:
            raise HTTPException(status_code=400, detail="You cannot add a friend")

        user_exists = await session.get(User, data_request.to_user_id)
        if not user_exists:
            raise HTTPException(status_code=400, detail="Friends does not exist")

        user_a, user_b = sorted((current_me.id, data.to_user_id))  # avoid duplicate

        stmt_friend = select(Friend).where(
            or_(
                (Friend.user_a == user_a) & (Friend.user_b == user_b),
                (Friend.user_a == user_b) & (Friend.user_a == user_a),
            )
        )
        friend_query = await session.exec(stmt_friend)
        already_friend = friend_query.first()
        if already_friend:
            raise HTTPException(status_code=400, detail="Already friends")

        stmt_request = select(FriendRequests).where(
            or_(
                (FriendRequests.from_user == user_a)
                & (FriendRequests.to_user_id == user_b),
                (FriendRequests.from_user == user_b)
                & (FriendRequests.to_user_id == user_a),
            )
        )
        request_query = await session.exec(stmt_request)
        exist_request = request_query.first()
        if exist_request:
            raise HTTPException(
                status_code=400, detail="There is a pending friend request"
            )

        new_request = FriendRequests(**data, from_user_id=current_me.id)
        session.add(new_request)
        await session.commit()
        return JSONResponse(status_code=201, content={"message": "Friend added"})
