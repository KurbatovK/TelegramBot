import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import Config
from bot.handlers import BaseHandler
from bot.db.db_init import init_db

#логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Инициализация бота...")
        
        #инициируем
        init_db()
        logger.info("Инициализируем БД...")
        
        #подключаем бота
        bot = Bot(token=Config.TOKEN)
        dp = Dispatcher()
        
        #подключение роутеров
        dp.include_router(BaseHandler.router)
        logger.info("Маршруты настроены...")
        
        #запуск
        logger.info("Бот запущен...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"Ошибка: {str(e)}", exc_info=True)
    finally:
        logger.info("Стоп бота")

if __name__ == "__main__":
    asyncio.run(main())