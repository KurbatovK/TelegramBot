import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from bot.handlers import router

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
