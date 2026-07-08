from aiogram import Dispatcher

from handlers.message_handler import router

dp = Dispatcher()

dp.include_router(router)