from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from .schema import CreateConvRequest, ConvType, ConversationResponse, ParticipantResponse, MessageResponse
from uuid import UUID
from sqlmodel import select, func, or_, and_, desc
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate

from ..core.model import Conversation, ConvParticipant, GroupConversation, Friend, ConvUnread, Message


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
                    raise HTTPException(
                        status_code=400,
                        detail="You can't create conversation with yourself",
                    )

                # Check friends list
                fr_stmt = select(Friend).where(
                    or_(
                        and_(
                            Friend.user_a == current_me,
                            Friend.user_b == data.member_id[0],
                        ),
                        and_(
                            Friend.user_b == current_me,
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

                other_user_id = data.member_id[0]

                # find existing direct conversation with BOTH users
                subq = (
                    select(ConvParticipant.conv_id)
                    .where(ConvParticipant.user_id.in_([current_me, other_user_id]))
                    .group_by(ConvParticipant.conv_id)
                    .having(func.count(ConvParticipant.user_id) == 2)
                    .subquery()
                )

                # Use a subquery to query that these two members belong to the direct type
                stmt = select(Conversation).where(
                    Conversation.type == ConvType.direct,
                    Conversation.id.in_(select(subq.c.conv_id)),
                )

                result = await session.exec(stmt)
                conv = result.first()

                if conv:
                    return conv

                # create new direct conversation
                conv = Conversation(type=ConvType.direct)
                session.add(conv)
                await session.flush()

                session.add_all(
                    [
                        ConvParticipant(conv_id=conv.id, user_id=current_me),
                        ConvParticipant(conv_id=conv.id, user_id=other_user_id),
                    ]
                )

                return conv

            # validate request fields for group type
            if data.type == ConvType.group:

                # validate requests fields
                if len(data.member_id) == 0:
                    raise HTTPException(status_code=400, detail="Member is required")
                if data.member_id[0] == current_me:
                    raise HTTPException(
                        status_code=400, detail="You can't create group with yourself"
                    )
                # Check friends list
                fr_stmt = select(Friend).where(
                    or_(Friend.user_a == current_me, Friend.user_b == current_me)
                )
                fr_query = await session.exec(fr_stmt)
                friends = fr_query.all()
                friend_ids: set[UUID] = set()
                for f in friends:
                    if f.user_a == current_me:
                        friend_ids.add(f.user_b)
                    else:
                        friend_ids.add(f.user_a)
                input_ids = set(data.member_id)
                if not input_ids.issubset(friend_ids):
                    raise HTTPException(
                        status_code=400, detail="Some members are not your friends!"
                    )

                conv = Conversation(type=ConvType.group)
                session.add(conv)
                await session.flush()

                session.add(
                    GroupConversation(
                        conv_id=conv.id,
                        name=data.name,
                        created_by=current_me,
                    )
                )

                participants = set(data.member_id)
                participants.add(current_me)

                session.add_all(
                    [
                        ConvParticipant(conv_id=conv.id, user_id=uid)
                        for uid in participants
                    ]
                )

                return conv

    async def get_all_conv(self, current_me: UUID, session: AsyncSession) -> Page[ConversationResponse]:
        stmt_conv = (
            select(Conversation)
            .join(ConvParticipant)
            .where(ConvParticipant.user_id == current_me)
            .options(
                selectinload(Conversation.conv_participants)
                .selectinload(ConvParticipant.user)
            )
            .order_by(Conversation.last_message_at.desc())
        )

        result = await session.exec(stmt_conv)
        convs = result.unique().all()

        if not convs:
            return []

        conv_ids = [conv.id for conv in convs]

        unread_stmt = (
            select(ConvUnread.conv_id, ConvUnread.unread_count)
            .where(
                ConvUnread.user_id == current_me,
                ConvUnread.conv_id.in_(conv_ids)
            )
        )

        unread_result = await session.exec(unread_stmt)
        unread_map = {
            conv_id: unread_count
            for conv_id, unread_count in unread_result.all()
        }

        responses: list[ConversationResponse] = []

        for conv in convs:
            participants = [
                ParticipantResponse(
                    user_id=p.user.id,
                    username=p.user.username,
                    avatar_url=p.user.avatar_url,
                    joined_at=p.joined_at,
                )
                for p in conv.conv_participants
                if p.user
            ]

            responses.append(
                ConversationResponse(
                    id=conv.id,
                    type=conv.type,
                    last_message_content=conv.last_message_content,
                    last_message_at=conv.last_message_at,
                    unread_count=unread_map.get(conv.id, 0),
                    participants=participants,
                )
            )

        return responses

    async def get_messages(self, conv_id: UUID, session: AsyncSession) -> Page[MessageResponse]:
        stmt = select(Message).where(Message.conv_id == conv_id)
        return await apaginate(session=session, query=stmt)

