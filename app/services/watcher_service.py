import asyncio

from config.settings import AUTO_CLOSE_MINUTES, CHECK_INTERVAL_SECONDS
from bot.bot import bot
from config.support import SUPPORT_CHAT_ID
from config.employees import SUPPORT_USERS
from database.database import update_sla_notification
from database.database import close_ticket
from database.database import get_inactive_tickets
from database.database import get_sla_violations
from config.settings import SLA_RESPONSE_MINUTES

mentions = " ".join(SUPPORT_USERS.values())

async def ticket_watcher():
    while True:
        try:
            inactive = await get_inactive_tickets(AUTO_CLOSE_MINUTES)
            for ticket in inactive:
                await close_ticket(ticket["id"])
                print(
                    f"🔒 Обращение {ticket['id']} автоматически закрыто"
                )
            sla = await get_sla_violations(SLA_RESPONSE_MINUTES)
            for ticket in sla:
                await update_sla_notification(ticket["id"])

                await bot.send_message(
                    SUPPORT_CHAT_ID,
                    f"🎫 Обращение #{ticket['id']}\n\n"
                    f"🔴 Нет ответа\n\n"
                    f"🏢 Клуб: {ticket['chat_title']}\n\n"
                    f"💬 {ticket['first_message']}\n\n"
                    f"👥 {mentions}"
                )

        except Exception as e:
            print(
                f"⚠️ Ошибка ticket_watcher: "
                f"{type(e).__name__}: {e}"
            )

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)