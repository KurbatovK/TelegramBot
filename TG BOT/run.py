import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import Config
from bot.handlers.handlers import router
from bot.database.db_init import init_db

async def main():
    bot = Bot(token=Config.TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

    init_db()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
