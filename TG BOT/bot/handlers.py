from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from bot.keyboards import (
    main_keyboard,
    program_keyboard,
    courses_keyboard,
    groups_keyboard
)

router = Router()

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Это команда /help')

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f'Привет, {message.from_user.first_name}, нажми на кнопку, которая тебе нужна!',
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data == 'teacher')
async def teacher(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Расписание какого преподавателя тебе нужно?')

@router.callback_query(F.data == 'schedule')
async def schedule(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Выбери свою программу обучения:',
        reply_markup=program_keyboard()
    )

@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        f'Привет, {callback.from_user.first_name}, нажми на кнопку которая тебе нужна!',
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data == 'bachelor')
async def bachelor_program(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Вы выбрали Бакалавриат. Теперь выберите курс:',
        reply_markup=courses_keyboard('bachelor')
    )

@router.callback_query(F.data == 'master')
async def master_program(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Вы выбрали Магистратуру. Теперь выберите курс:',
        reply_markup=courses_keyboard('master')
    )

@router.callback_query(F.data.startswith('bachelor_'))
async def bachelor_year(callback: CallbackQuery):
    await callback.answer()
    year = callback.data.split('_')[1]
    await callback.message.edit_text(
        f'Вы выбрали {year} курс бакалавриата. Теперь выберите группу:',
        reply_markup=groups_keyboard(f'bachelor_{year}')
    )

@router.callback_query(F.data.startswith('master_'))
async def master_year(callback: CallbackQuery):
    await callback.answer()
    year = callback.data.split('_')[1]
    await callback.message.edit_text(
        f'Вы выбрали {year} курс магистратуры. Теперь выберите группу:',
        reply_markup=groups_keyboard(f'master_{year}')
    )

@router.callback_query(F.data == 'back_to_programs')
async def back_to_programs(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Выбери свою программу обучения:',
        reply_markup=program_keyboard()
    )



