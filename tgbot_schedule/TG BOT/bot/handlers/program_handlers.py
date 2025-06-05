from aiogram import F
from aiogram.types import CallbackQuery
from .base_handlers import BaseHandler
from ..keyboards.keyboards import (
    program_keyboard,
    courses_keyboard,
    groups_keyboard
)

class ProgramHandlers(BaseHandler):
    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'schedule')
    async def schedule(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Выбери свою программу обучения:',
            reply_markup=program_keyboard()
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'bachelor')
    async def bachelor_program(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Вы выбрали Бакалавриат. Теперь выберите курс:',
            reply_markup=courses_keyboard('bachelor')
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'master')
    async def master_program(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Вы выбрали Магистратуру. Теперь выберите курс:',
            reply_markup=courses_keyboard('master')
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('bachelor_'))
    async def bachelor_year(callback: CallbackQuery) -> None:
        await callback.answer()
        year = callback.data.split('_')[1]
        await callback.message.edit_text(
            f'Вы выбрали {year} курс бакалавриата. Теперь выберите группу:',
            reply_markup=groups_keyboard(f'bachelor_{year}')
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('master_'))
    async def master_year(callback: CallbackQuery) -> None:
        await callback.answer()
        year = callback.data.split('_')[1]
        await callback.message.edit_text(
            f'Вы выбрали {year} курс магистратуры. Теперь выберите группу:',
            reply_markup=groups_keyboard(f'master_{year}')
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'back_to_programs')
    async def back_to_programs(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Выбери свою программу обучения:',
            reply_markup=program_keyboard()
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'back_to_bachelor')
    async def back_to_bachelor_courses(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Вы выбрали Бакалавриат. Теперь выберите курс:',
            reply_markup=courses_keyboard('bachelor')
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'back_to_master')
    async def back_to_master_courses(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            'Вы выбрали Магистратуру. Теперь выберите курс:',
            reply_markup=courses_keyboard('master')
        )