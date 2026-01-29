from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from .schema import CreateConvRequest, ConvType
from uuid import UUID
from sqlmodel import select, func

from ..core.model import Conversation, ConvParticipant, GroupConversation, User, Friend


class ConvServices:
    async def create_conv(
            self,
            current_me: UUID,
            data: CreateConvRequest,
            session: AsyncSession,
    ):
        if not data.member_id:
            raise HTTPException(status_code=400, detail="Member is required")

        if data.type == ConvType.group and not data.name:
            raise HTTPException(status_code=400, detail="Group name is required")

        async with session.begin():
            # validate request fields for the direct type
            if data.type == ConvType.direct:
                if len(data.member_id) != 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Direct conversation must have exactly 1 member",
                    )
                if data.member_id[0] == current_me:
                    raise HTTPException(status_code=400, detail="You can't create conversation with yourself")

                # Check friend list
                fr_stmt = select(Friend).where((Friend.user_a == data.member_id) | (Friend.user_b == data.member_id))



            #     other_user_id = data.member_id[0]
            #
            #     # find existing direct conversation with BOTH users
            #     subq = (
            #         select(ConvParticipant.conv_id)
            #         .where(ConvParticipant.user_id.in_([current_me, other_user_id]))
            #         .group_by(ConvParticipant.conv_id)
            #         .having(func.count(ConvParticipant.user_id) == 2)
            #         .subquery()
            #     )
            #
            #     # Use a subquery to query that these two members belong to the direct type
            #     stmt = (
            #         select(Conversation)
            #         .where(
            #             Conversation.type == ConvType.direct,
            #             Conversation.id.in_(select(subq.c.conv_id)),
            #         )
            #     )
            #
            #     result = await session.exec(stmt)
            #     conv = result.first()
            #
            #     if conv:
            #         return conv
            #
            #     # create new direct conversation
            #     conv = Conversation(type=ConvType.direct)
            #     session.add(conv)
            #     await session.flush()
            #
            #     session.add_all(
            #         [
            #             ConvParticipant(conv_id=conv.id, user_id=current_me),
            #             ConvParticipant(conv_id=conv.id, user_id=other_user_id),
            #         ]
            #     )
            #
            #     return conv
            #
            # # validate request fields for group type
            # if data.type == ConvType.group:
            #     if len(data.member_id) == 0:
            #         raise HTTPException(status_code=400, detail="Member is required")
            #     if data.member_id[0] == current_me:
            #         raise HTTPException(status_code=400, detail="You can't create group with yourself")
            #
            #     conv = Conversation(type=ConvType.group)
            #     session.add(conv)
            #     await session.flush()
            #
            #     session.add(
            #         GroupConversation(
            #             conv_id=conv.id,
            #             name=data.name,
            #             created_by=current_me,
            #         )
            #     )
            #
            #     participants = set(data.member_id)
            #     participants.add(current_me)
            #
            #     session.add_all(
            #         [
            #             ConvParticipant(conv_id=conv.id, user_id=uid)
            #             for uid in participants
            #         ]
            #     )
            #
            #     return conv



