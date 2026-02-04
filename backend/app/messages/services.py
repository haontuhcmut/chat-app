from uuid import UUID

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from .schema import CreateMessage
from ..conversations.schema import ConvType
from ..core.model import Conversation, ConvParticipant, Message
from ..friends.services import FriendshipService


class MessageService:

    async def send_direct_message(
        self,
        data: CreateMessage,
        friendship: FriendshipService,
        current_me: UUID,
        session: AsyncSession,
    ):
        if not data.content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        await friendship.assert_direct_friend(
            user_id=current_me, target_id=data.recipient_id, session=session
        )
        conv = await session.get(Conversation, data.conv_id)
        if not conv:
            # create new direct conversation
            conv = Conversation(type=ConvType.direct)
            session.add(conv)
            await session.flush()

            session.add_all(
                [
                    ConvParticipant(conv_id=conv.id, user_id=current_me),
                    ConvParticipant(conv_id=conv.id, user_id=data.recipient_id),
                ]
            )
        new_message = Message(
            conv_id=conv.id,
            sender_user_id=current_me,
            content=data.content,
            img_url=data.img_url,
        )
        session.add(new_message)
        await session.flush()

        conv.last_message_at = new_message.updated_at
        conv.last_message_sender_id = new_message.sender_user_id
        conv.last_message_content = new_message.content
        session.add(conv)
        await session.commit()

        return new_message
