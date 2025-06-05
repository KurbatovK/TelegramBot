from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from .base_handlers import BaseHandler
from ..keyboards.keyboards import main_keyboard

class CommandHandlers(BaseHandler):
    @staticmethod
    @BaseHandler.router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            f'Привет, {message.from_user.first_name}! Я бот, который знает твоё расписание лучше деканата 😉 Выбирай свою группу — больше не пропустишь ни одной пары!',
            reply_markup=main_keyboard()
        )

    @staticmethod
    @BaseHandler.router.message(Command('help'))
    async def cmd_help(message: Message) -> None:
        await message.answer('Это команда /help')

    @staticmethod
    @BaseHandler.router.message(Command('creators'))
    async def cmd_creators(message: Message) -> None:
        await message.answer('@ixzez - Кирюха норм пацан \n@wepine - Вип бурятка')

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'information')
    async def information(callback: CallbackQuery) -> None:
        info_text = """
🌟 <b>Универ-Помощник - ваш персональный ассистент</b> 🌟

Я помогу вам всегда быть в курсе расписания! 
Мгновенный доступ к актуальному расписанию пар, аудиториям и изменениям.

🚀 <b>Основные возможности:</b>
▫️ Удобное меню с интерактивными кнопками
▫️ Расписание по группам и преподавателям
▫️ Выбор программы:
   → Бакалавриат/Магистратура
   → Курс и группа
   → День недели (сегодня/завтра/неделя)
▫️ Автоматическое обновление данных

👥 <b>Для кого я?</b>
✔ Студентам - больше не искать расписание в чатах!
✔ Преподавателям - быстрый доступ к графику
✔ Администрации - удобное управление

✨ <b>Преимущества:</b>
✅ Экономия времени - вся информация в 2 клика
✅ Работаю 24/7 - отвечу даже ночью
✅ Простота - разберётся любой первокурсник

📌 <b>Пример использования:</b>
1. Выбери группу
2. Укажи курс 
3. Получай чёткое расписание с аудиториями!

<i>Начните работу командой /start</i>
"""
        await callback.answer()
        await callback.message.answer(
            text=info_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'back_to_main')
    async def back_to_main(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            f'Привет, {callback.from_user.first_name}! Я бот, который знает твоё расписание лучше деканата 😉 Выбирай свою группу — больше не пропустишь ни одной пары!',
            reply_markup=main_keyboard()
        )