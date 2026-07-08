import asyncio
import logging

from bot.bot import bot
from bot.dispatcher import dp
from services.watcher_service import ticket_watcher
from database.database import connect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


async def main():
    logging.info("SupportBot started")
    await connect()
    asyncio.create_task(ticket_watcher())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())