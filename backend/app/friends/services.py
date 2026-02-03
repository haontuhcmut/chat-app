from uuid import UUID

from fastapi import HTTPException
from pygments.lexers import data
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_, and_
from fastapi.responses import JSONResponse

from .schema import (
    NewFriendResponse,
    AllFriendsResponse,
    AllFriendsRequest,
    SentReceivedFriendsRequest,
)
from ..core.model import User, FriendRequests, Friend
from ..friends.schema import AddFriendSchema
import logging

class FriendServices:
    async def add_friend(
        self,
        current_me: UUID,
        data_request: AddFriendSchema,
        session: AsyncSession,
    ):

        data = data_request.model_dump()
        if data_request.to_user_id == current_me:
            raise HTTPException(
                status_code=400, detail="You cannot send a friend request to yourself"
            )

        user_exists = await session.get(User, data_request.to_user_id)
        if not user_exists:
            raise HTTPException(status_code=400, detail="User does not exist")

        user_a, user_b = sorted((current_me, data["to_user_id"]))  # normalization

        stmt_friend = select(Friend).where(
            Friend.user_a == user_a,
            Friend.user_b == user_b,
        )
        friend_query = await session.exec(stmt_friend)
        already_friend = friend_query.first()
        if already_friend:
            raise HTTPException(status_code=400, detail="Already friends")

        stmt_request = select(FriendRequests).where(
            or_(
                (FriendRequests.from_user_id == user_a)
                & (FriendRequests.to_user_id == user_b),
                (FriendRequests.from_user_id == user_b)
                & (FriendRequests.to_user_id == user_a),
            )
        )
        request_query = await session.exec(stmt_request)
        exist_request = request_query.first()
        if exist_request:
            raise HTTPException(
                status_code=400, detail="There is a pending friend request"
            )

        new_request = FriendRequests(**data, from_user_id=current_me)
        session.add(new_request)
        await session.commit()
        return JSONResponse(
            status_code=201,
            content={"message": "Your request has been successfully sent"},
        )

    async def accept_request_friend(
        self, current_me: UUID, request_id: str, session: AsyncSession
    ):
        async with session.begin():
            # id check request by id
            request = await session.get(FriendRequests, UUID(request_id))
            if not request:
                raise HTTPException(status_code=404, detail="Request not found")

            if request.to_user_id != current_me:
                raise HTTPException(403, "You are not allowed to accept this request")

            # Create new friend
            user_a, user_b = sorted(
                (request.from_user_id, request.to_user_id)
            )  # normalization
            new_friend = Friend(user_a=user_a, user_b=user_b)
            session.add(new_friend)
            await session.delete(request)

            # Get user request
            from_user = await session.get(User, request.from_user_id)

        return NewFriendResponse(
            from_user_id=from_user.id,
            user_name=from_user.username,
            avatar_url=from_user.avatar_url,
        )

    async def decline_request_friend(
        self, current_me: UUID, request_id: str, session: AsyncSession
    ):
        request = await session.get(FriendRequests, UUID(request_id))
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.to_user_id != current_me:
            raise HTTPException(403, "You are not allowed to decline this request")
        await session.delete(request)
        await session.commit()
        return []

    async def get_all_friends(
        self, current_me: UUID, session: AsyncSession
    ) -> list[AllFriendsResponse]:
        stmt = (
            select(Friend)
            .where(
                or_(
                    Friend.user_a == current_me,
                    Friend.user_b == current_me,
                )
            )
            .options(selectinload(Friend.user_a_rel), selectinload(Friend.user_b_rel))
        )
        friends_query = await session.exec(stmt)
        results = friends_query.all()

        friends: list[AllFriendsResponse] = []
        for f in results:
            if f.user_a == current_me:
                friend = f.user_b_rel
            else:
                friend = f.user_a_rel

            friends.append(
                AllFriendsResponse(
                    id=f.id,
                    user_id=friend.id,
                    username=friend.username,
                    avatar_url=friend.avatar_url,
                )
            )
        return friends

    async def get_friend_requests(
        self, current_me: UUID, session: AsyncSession
    ) -> SentReceivedFriendsRequest:
        # Sent requests (from me -> others)
        stmt_sent = (
            select(FriendRequests)
            .where(FriendRequests.from_user_id == current_me)
            .options(selectinload(FriendRequests.to_user))
        )

        # Received request (other -> me)
        stmt_received = (
            select(FriendRequests)
            .where(FriendRequests.to_user_id == current_me)
            .options(selectinload(FriendRequests.from_user))
        )

        sent_results = await session.exec(stmt_sent)
        received_results = await session.exec(stmt_received)

        sent_requests = sent_results.all()
        received_requests = received_results.all()

        sent: list[AllFriendsRequest] = []
        received: list[AllFriendsResponse] = []

        for req in sent_requests:
            user = req.to_user
            sent.append(
                AllFriendsRequest(
                    id= req.id, user_id=user.id, username=user.username, avatar_url=user.avatar_url
                )
            )

        for req in received_requests:
            user = req.from_user
            received.append(
                AllFriendsRequest(
                   id= req.id, user_id=user.id, username=user.username, avatar_url=user.avatar_url
                )
            )

        return SentReceivedFriendsRequest(sent=sent, received=received)

class FriendshipService:
    async def assert_direct_friend(self, user_id: UUID, target_id: UUID, session: AsyncSession):
        if user_id == target_id:
            raise HTTPException(400, "You can't create conversation with yourself")

        stmt = select(Friend).where(
            or_(
                and_(Friend.user_a == user_id, Friend.user_b == target_id),
                and_(Friend.user_b == user_id, Friend.user_a == target_id),
            )
        )
        result = await session.exec(stmt)
        if not result.first():
            raise HTTPException(400, "You are not friends with this person yet")

    async def assert_group_friends(self, user_id: UUID, member_ids: list[UUID], session: AsyncSession):
        if not member_ids:
            raise HTTPException(400, "Member is required")

        stmt = select(Friend).where(
            or_(Friend.user_a == user_id, Friend.user_b == user_id)
        )
        result = await session.exec(stmt)
        friends = result.all()

        friend_ids = {
            f.user_b if f.user_a == user_id else f.user_a
            for f in friends
        }

        if not set(member_ids).issubset(friend_ids):
            raise HTTPException(400, "Some members are not your friends!")
