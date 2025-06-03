import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import Config
from bot.handlers.handlers import router
from bot.db.db_init import init_db

#логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Starting bot initialization...")
        
        #инициируем бд
        init_db()
        logger.info("Database initialized")
        
        #создание и подключение бота
        bot = Bot(token=Config.TOKEN)
        dp = Dispatcher()
        
        #подключение роутеров
        dp.include_router(router)
        logger.info("Router configured")
        
        #запуск бота
        logger.info("Bot started polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())