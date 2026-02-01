from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from fastapi.params import Depends, Body
from sqlmodel import select, or_, and_

from ..auth.dependency import AccessTokenBearer
from ..conversations.schema import CreateConvRequest, ConvType
from ..core.dependency import SessionDep
from ..core.model import Friend


async def require_friendships(
    current_me: Annotated[dict, Depends(AccessTokenBearer())],
    data: Annotated[CreateConvRequest, Body()],
    session: SessionDep,
):
    user_id = UUID(current_me.get("user_id"))
    # validate request fields for the direct type
    if data.type == ConvType.direct:
        if len(data.member_id) != 1:
            raise HTTPException(
                status_code=400,
                detail="Direct conversation must have exactly 1 member",
            )
        if data.member_id[0] == user_id:
            raise HTTPException(
                status_code=400,
                detail="You can't create conversation with yourself",
            )
        fr_stmt = select(Friend).where(
            or_(
                and_(
                    Friend.user_a == user_id,
                    Friend.user_b == data.member_id[0],
                ),
                and_(
                    Friend.user_b == user_id,
                    Friend.user_a == data.member_id[0],
                ),
            )
        )
        fr_query = await session.exec(fr_stmt)
        exist_fr = fr_query.first()
        if not exist_fr:
            raise HTTPException(
                status_code=400,
                detail="You are not friends with this person yet",
            )

    # validate request fields for group type
    if data.type == ConvType.group:
        # validate requests fields
        if len(data.member_id) == 0:
            raise HTTPException(status_code=400, detail="Member is required")
        if data.member_id[0] == user_id:
            raise HTTPException(
                status_code=400, detail="You can't create group with yourself"
            )
        # Check friends list
        fr_stmt = select(Friend).where(
            or_(Friend.user_a == user_id, Friend.user_b == user_id)
        )
        fr_query = await session.exec(fr_stmt)
        friends = fr_query.all()
        friend_ids: set[UUID] = set()
        for f in friends:
            if f.user_a == user_id:
                friend_ids.add(f.user_b)
            else:
                friend_ids.add(f.user_a)
        input_ids = set(data.member_id)
        if not input_ids.issubset(friend_ids):
            raise HTTPException(
                status_code=400, detail="Some members are not your friends!"
            )

    return True
