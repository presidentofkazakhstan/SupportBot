from aiogram import Router
from aiogram.types import Message

from database.database import (
    create_ticket,
    update_first_response,
    update_last_activity,
)
from database.database import get_open_ticket
from config.employees import SUPPORT_USERS
from config.support import IGNORE_USERS
from database.database import has_open_ticket
from database.database import get_first_response_seconds

router = Router()


@router.message()
async def all_messages(message: Message):
    if (
        message.new_chat_members
        or message.left_chat_member
        or message.group_chat_created
        or message.supergroup_chat_created
        or message.channel_chat_created
        or message.pinned_message
    ):
        return

    if not (message.text or message.caption):
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in IGNORE_USERS:
        return

    is_support = user_id in SUPPORT_USERS

    if is_support:

        sla_ticket = await get_first_response_seconds(chat_id)

        response_time = None

        if sla_ticket and not sla_ticket["sla_completed"]:
            response_time = sla_ticket["response_time"]

        ticket = await get_open_ticket(chat_id)
        if ticket:
            await update_last_activity(ticket["id"])

        if response_time is not None:
            await update_first_response(
                ticket["id"],
                response_time
            )
            print(f"✅ Первый ответ ({response_time} сек.)")
        else:
            print("💬 Ответ сотрудника")

    else:
        if await has_open_ticket(chat_id):
            ticket = await get_open_ticket(chat_id)
            if ticket:
                await update_last_activity(ticket["id"])
            print("💬 Сообщение в существующем обращении")
        else:
            ticket_id = await create_ticket(
                chat_id,
                message.chat.title,
                message.text or "Без текста"
            )

            print("🆕 Новое обращение")
