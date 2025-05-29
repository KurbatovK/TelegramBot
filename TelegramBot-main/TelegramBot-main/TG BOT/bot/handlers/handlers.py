from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from bot.db.db_utils import get_cached, save_to_db
from ..api.api_serv import fetch_schedule_from_api
from config import Config
from ..keyboards.keyboards import (
    main_keyboard,
    program_keyboard,
    courses_keyboard,
    groups_keyboard,
    day_selection_keyboard
)

router = Router()

def format_schedule(schedule_data):
    if not schedule_data:
        return "Расписание не найдено"

    days = {}
    for item in schedule_data:
        day = item['weekday']
        if day not in days:
            days[day] = []
        days[day].append(item)

    result = []
    for day, pairs in days.items():
        day_schedule = f"<b>{day.capitalize()}</b>\n"
        for pair in sorted(pairs, key=lambda x: x['pair_start_time']):
            day_schedule += (
                f"⏰ {pair['pair_start_time']}-{pair['pair_end_time']}\n"
                f"📚 {pair['subject_name']} ({pair['pair_type']})\n"
                f"👨‍🏫 {pair.get('teacher', 'Преподаватель не указан')}\n"
                f"🚪 {pair.get('class_name', 'Аудитория не указана')}\n\n"
            )
        result.append(day_schedule)

    return "\n".join(result) if result else "На этот день пар нет"

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f'Привет, {message.from_user.first_name}! Я бот, который знает твоё расписание лучше деканата 😉 Выбирай свою группу — больше не пропустишь ни одной пары!',
        reply_markup=main_keyboard()
    )

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Это команда /help')

@router.message(Command('creators'))
async def cmd_creators(message: Message):
    await message.answer('@ixzez - Кирюха норм пацан \n@wepine - Вип бурятка')

@router.callback_query(F.data == 'information')
async def information(callback: CallbackQuery):
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
        f'Привет, {callback.from_user.first_name}! Я бот, который знает твоё расписание лучше деканата 😉 Выбирай свою группу — больше не пропустишь ни одной пары!',
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

@router.callback_query(F.data == 'back_to_bachelor')
async def back_to_bachelor_courses(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Вы выбрали Бакалавриат. Теперь выберите курс:',
        reply_markup=courses_keyboard('bachelor')
    )

@router.callback_query(F.data == 'back_to_master')
async def back_to_master_courses(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Вы выбрали Магистратуру. Теперь выберите курс:',
        reply_markup=courses_keyboard('master')
    )

@router.callback_query(F.data.startswith('group_'))
async def select_day(callback: CallbackQuery):
    await callback.answer()
    _, group_name, program_year = callback.data.split('_', 2)
    await callback.message.edit_text(
        f'Выбери день для группы {group_name}:',
        reply_markup=day_selection_keyboard(group_name, program_year)
    )

@router.callback_query(F.data.startswith('day_'))
async def show_schedule(callback: CallbackQuery):
    await callback.answer()
    _, day_type, group_name, program_year = callback.data.split('_', 3)

    date_map = {
        'today': datetime.now().strftime('%Y-%m-%d'),
        'tomorrow': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'week': 'week'
    }

    query_params = {
        'date': date_map[day_type],
        'group': group_name,
        'teacher': ''
    }

    cached_data = get_cached(query_params)

    if cached_data:
        schedule_text = format_schedule(cached_data)
    else:
        api_data = await fetch_schedule_from_api(query_params)
        if api_data:
            save_to_db(api_data, query_params)
            schedule_text = format_schedule(api_data)
        else:
            schedule_text = "Не удалось получить расписание"

    day_display = {
        'today': 'на сегодня',
        'tomorrow': 'на завтра',
        'week': 'на неделю'
    }

    await callback.message.edit_text(
        f"📅 Расписание группы {group_name} {day_display[day_type]}:\n\n{schedule_text}",
        parse_mode="HTML"
    )
