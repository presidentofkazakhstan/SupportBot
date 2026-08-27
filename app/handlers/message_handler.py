from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

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
from database.database import get_employee_by_telegram_id
from database.database import get_statistics
from config.employees import SUPPORT_USERS
from config.support import SUPPORT_CHAT_ID

router = Router()

@router.message(Command("stats"))
async def statistics(message: Message):

    if message.chat.id != SUPPORT_CHAT_ID:
        return

    if message.from_user.id not in SUPPORT_USERS:
        return

    employees, sla_violations, total_tickets = await get_statistics()
    sla_without_violations = total_tickets - sla_violations

    text = "📊 Статистика за текущий месяц\n\n"

    text += f"🎫 Всего обращений: {total_tickets}\n\n"

    text += f"🟢 Без нарушения: {sla_without_violations}\n"
    text += f"🔴 Нарушений: {sla_violations}\n\n"

    text += "👥 Ответы сотрудников:\n"

    for i, employee in enumerate(employees, start=1):
        avg_seconds = employee["avg_response_seconds"]

        if avg_seconds is not None:
            avg_seconds = int(avg_seconds)

            minutes = avg_seconds // 60
            seconds = avg_seconds % 60

            if minutes > 0:
                avg_time = f"{minutes}м {seconds}с"
            else:
                avg_time = f"{seconds}с"
        else:
            avg_time = "нет данных"

        text += (
            f"{i}. {employee['full_name']} : "
            f"{employee['answered_tickets']}\n"
            f"   ⏱ Средний ответ: {avg_time}\n\n"
        )
    await message.answer(text)

def is_thanks_message(text):
    if not text:
        return False

    text = text.lower().strip()

    return "спасибо" in text or "благодарю" in text

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

    if not (message.text or message.caption or message.voice):
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
            employee = await get_employee_by_telegram_id(
                 message.from_user.id
            )

            if employee:
                await update_first_response(
                    ticket["id"],
                    response_time,
                    employee["id"]
                )
                print(
                    f"✅ Первый ответ ({response_time} сек.) "
                    f"сотрудник ID={employee['id']}"
                )
            else:
                 print(
                    f"⚠️ Сотрудник {message.from_user.id} "
                    f"не найден в employees"
                )
        else:
            print("💬 Ответ сотрудника")

    else:
        if await has_open_ticket(chat_id):
            ticket = await get_open_ticket(chat_id)
            if ticket:
                await update_last_activity(ticket["id"])
            print("💬 Сообщение в существующем обращении")
        else:
            text = message.text or message.caption or ""

            if is_thanks_message(text):
                print("🙏 Благодарность клуба — новое обращение не создаём")
                return
            if message.text:
                first_message = message.text
            elif message.caption:
                first_message = message.caption
            elif message.voice:
                first_message = "🎤 Голосовое сообщение"
            else:
                first_message = "Без текста"

            ticket_id = await create_ticket(
                chat_id,
                message.chat.title,
                first_message
            )

            print(f"🆕 Новое обращение | Клуб: {message.chat.title}")