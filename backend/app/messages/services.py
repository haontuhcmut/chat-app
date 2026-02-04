from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .schema import CreateMessage
from ..conversations.schema import ConvType
from ..core.model import Conversation, ConvParticipant, Message, ConvUnread
from ..friends.services import FriendshipService


class MessageService:
    async def send_direct_message(
        self,
        data: CreateMessage,
        current_me: UUID,
        friendship: FriendshipService,
        session: AsyncSession,
    ) -> Message:
        # Validate
        if not data.content and not data.img_url:
            raise HTTPException(
                status_code=400, detail="Message must have content or image"
            )

        # Check friendship
        await friendship.assert_direct_friend(
            user_id=current_me, target_id=data.recipient_id, session=session
        )

        # Find existing direct conversation (STRICT)
        stmt = (
            select(Conversation)
            .join(ConvParticipant)
            .where(
                Conversation.type == ConvType.direct,
                ConvParticipant.user_id.in_([current_me, data.recipient_id]),
            )
            .group_by(Conversation.id)
            .having(func.count(ConvParticipant.user_id) == 2)
            .limit(1)
        )
        conv = await session.scalar(stmt)

        # Create conversation if not exists
        if not conv:
            conv = Conversation(type=ConvType.direct)
            session.add(conv)
            await session.flush()  # get conv_id

            session.add_all(
                [
                    ConvParticipant(
                        conv_id=conv.id,
                        user_id=current_me,
                    ),
                    ConvParticipant(
                        conv_id=conv.id,
                        user_id=data.recipient_id,
                    ),
                    ConvUnread(conv_id=conv.id, user_id=current_me, unread_count=1),
                    ConvUnread(
                        conv_id=conv.id, user_id=data.recipient_id, unread_count=1
                    ),
                ]
            )

        # Create message
        message = Message(
            conv_id=conv.id,
            sender_user_id=current_me,
            content=data.content,
            img_url=data.img_url,
        )
        session.add(message)
        await session.flush()

        # Update conversation metadata
        conv.last_message_at = message.created_at
        conv.last_message_sender_id = current_me
        conv.last_message_content = message.content if message.content else "[image]"
        session.add(conv)

        # Update unread
        unread_stmt = select(ConvUnread).where(
            ConvUnread.conv_id == conv.id, ConvUnread.user_id == data.recipient_id
        )
        result = await session.exec(unread_stmt)
        unread_count = result.one()
        unread_count.unread_count += 1
        session.add(unread_count)
        await session.commit()
        return message


