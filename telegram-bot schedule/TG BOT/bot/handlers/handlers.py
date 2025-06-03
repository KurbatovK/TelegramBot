import asyncio
import logging
from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from bot.db.db_utils import (
    get_cached,
    save_to_db
)
from ..api.api_serv import APIClient
from config import Config
from ..keyboards.keyboards import (
    main_keyboard,
    program_keyboard,
    courses_keyboard,
    groups_keyboard,
    day_selection_keyboard
)

logger = logging.getLogger(__name__)

router = Router()

class ClassroomStates(StatesGroup):
    waiting_for_classroom_name = State()
    waiting_for_period = State()

class TeacherStates(StatesGroup):
    waiting_for_teacher_name = State()
    waiting_for_period = State()

async def send_long_message(message: Message, text: str, **kwargs):
    max_length = 4096

    if len(text) <= max_length:
        return await message.answer(text, **kwargs)

    # Разбиваем текст на части
    parts = []
    while text:
        part = text[:max_length]
        # Находим последний перенос строки в части
        last_newline = part.rfind('\n')
        if last_newline > 0:
            part = part[:last_newline]
            remaining = text[last_newline+1:]
        else:
            remaining = text[max_length:]

        parts.append(part)
        text = remaining

    # Отправляем части по очереди
    for part in parts:
        await message.answer(part, **kwargs)
        await asyncio.sleep(0.5)  # Небольшая пауза между сообщениями

def _base_schedule_formatter(
    items: list,
    title: str,
    pair_formatter: callable,
    empty_message: str = "Данные не найдены"
) -> str:
    """Базовая функция форматирования расписания.
    
    Args:
        items: Список элементов расписания
        title: Заголовок (например, "Расписание группы")
        pair_formatter: Функция для форматирования одной пары
        empty_message: Сообщение при отсутствии данных
    """
    if not items:
        return empty_message

    # Группируем по дням недели
    days = {}
    for item in items:
        day = item['weekday']
        if day not in days:
            days[day] = []
        days[day].append(item)

    # Сортируем дни по порядку
    week_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                 'Пятница', 'Суббота', 'Воскресенье']
    sorted_days = sorted(days.items(), 
                        key=lambda x: week_order.index(x[0]) if x[0] in week_order else 7)

    result = []
    for day, pairs in sorted_days:
        day_header = f"<b>📌 {day.upper()}</b>\n"
        day_schedule = []

        for pair in sorted(pairs, key=lambda x: x['pair_start_time']):
            formatted_pair = pair_formatter(pair)
            day_schedule.append("\n".join(formatted_pair))

        if day_schedule:
            # Добавляем разделители между парами
            day_schedule_with_seps = []
            for i, pair in enumerate(day_schedule):
                day_schedule_with_seps.append(pair)
                if i < len(day_schedule) - 1:
                    day_schedule_with_seps.append("    ───────────────")
            
            result.append(day_header + "\n".join(day_schedule_with_seps))

    return "\n\n".join(result) if result else empty_message

# Форматирует расписание для студентов
def format_schedule(schedule_data: list) -> str:
    def formatter(pair):
        return [
            f"    ⏰ {pair['pair_start_time']}-{pair['pair_end_time']}",
            f"    📚 {pair['subject_name']} ({pair['pair_type']})",
            f"    👨‍🏫 {pair.get('teacher', 'Преподаватель не указан')}",
            f"    🚪 {pair.get('class_name', 'Аудитория не указана')}"
        ]
    
    return _base_schedule_formatter(
        schedule_data,
        title="Расписание группы",
        pair_formatter=formatter,
        empty_message="На этот период пар нет"
    )

# Форматирует расписание для преподавателей
def format_teacher_schedule(found_pairs: list) -> str:
    def formatter(pair):
        return [
            f"    ⏰ {pair['pair_start_time'].replace('.', ':')}-{pair['pair_end_time'].replace('.', ':')}",
            f"    📚 {pair['subject_name']} ({pair['pair_type']})",
            f"    🚪 Ауд. {pair['class_name']}",
            f"    👥 Группа: {pair['group_name']}"
        ]
    
    return _base_schedule_formatter(
        found_pairs,
        title="Расписание преподавателя",
        pair_formatter=formatter,
        empty_message="Пары не найдены"
    )

# Форматирует расписание для аудитории
def format_classroom_schedule(found_pairs: list) -> str:
    def formatter(pair):
        return [
            f"    ⏰ {pair['pair_start_time'].replace('.', ':')}-{pair['pair_end_time'].replace('.', ':')}",
            f"    📚 {pair['subject_name']} ({pair['pair_type']})",
            f"    👨‍🏫 {pair['teacher']}",
            f"    👥 Группа: {pair['group_name']}"
        ]
    
    return _base_schedule_formatter(
        found_pairs,
        title="Расписание аудитории",
        pair_formatter=formatter,
        empty_message="Аудитория свободна"
    )

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


#Обработчик кнопки поиска по преподавателю
@router.callback_query(F.data == 'teacher')
async def handle_teacher_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки поиска по преподавателю"""
    await callback.message.answer(
        "🔍 Введите фамилию преподавателя (например: <i>Ильин</i> или <i>Ильин Б.П.</i>):",
        parse_mode="HTML"
    )
    await state.set_state(TeacherStates.waiting_for_teacher_name)
    await callback.answer()

#Запрашивает у пользователя период для поиска
async def ask_for_period(message: Message, teacher_name: str, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Сегодня", callback_data=f"teacher_today_{teacher_name}"),
        InlineKeyboardButton(text="Завтра", callback_data=f"teacher_tomorrow_{teacher_name}"),
        InlineKeyboardButton(text="Неделя", callback_data=f"teacher_week_{teacher_name}"),
    )
    builder.adjust(2, 1)

    await message.answer(
        f"Вы ищете преподавателя: <b>{teacher_name}</b>. Выберите период:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.clear()

#обработчик ввода имени преподавателя
@router.message(TeacherStates.waiting_for_teacher_name)
async def process_teacher_name(message: Message, state: FSMContext):
    teacher_name = message.text.strip()
    if len(teacher_name) < 3:
        await message.answer("❌ Слишком короткий запрос. Введите фамилию преподавателя (минимум 3 символа).")
        return

    await ask_for_period(message, teacher_name, state)

#Обработчик выбора периода для преподавателя
@router.callback_query(F.data.startswith('teacher_'))
async def process_teacher_period(callback: CallbackQuery):
    await callback.answer()
    
    try:
        _, period_type, teacher_name = callback.data.split('_', maxsplit=2)
        
        today = datetime.now().date()
        if period_type == 'today':
            dates = [today]
            period_text = "на сегодня"
        elif period_type == 'tomorrow':
            dates = [today + timedelta(days=1)]
            period_text = "на завтра"
        else:
            dates = [today + timedelta(days=i) for i in range(7)]
            period_text = "на неделю"

        all_groups = Config.GROUPS
        
        async with APIClient() as client:
            # Используем новый метод
            batch_data = await client.fetch_batch_schedules(
                date_list=[d.strftime('%Y-%m-%d') for d in dates],
                group_list=all_groups
            )
        
        found_pairs = []
        for data in batch_data.values():
            if data:
                for pair in data:
                    if (teacher_name.lower() in pair['teacher'].lower() or
                        teacher_name.lower() in pair.get('lastname', '').lower()):
                        found_pairs.append(pair)

        if found_pairs:
            schedule_text = format_teacher_schedule(found_pairs)
            response = f"<b>📅 Расписание преподавателя {teacher_name} {period_text}:</b>\n\n{schedule_text}"
        else:
            response = f"❌ Преподаватель {teacher_name} не найден в расписании {period_text}."

        await send_long_message(callback.message, response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in teacher schedule: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при получении расписания")

@router.callback_query(F.data == 'classroom')
async def handle_classroom_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки поиска по аудитории"""
    await callback.message.answer(
        "🔍 Введите номер аудитории (например: <i>113-3</i> или <i>312а</i>):",
        parse_mode="HTML"
    )
    await state.set_state(ClassroomStates.waiting_for_classroom_name)
    await callback.answer()

@router.message(ClassroomStates.waiting_for_classroom_name)
async def process_classroom_name(message: Message, state: FSMContext):
    classroom_name = message.text.strip().upper()
    
    if len(classroom_name) < 2:
        await message.answer("❌ Слишком короткий запрос. Введите номер аудитории (минимум 2 символа).")
        return

    await state.update_data(classroom_name=classroom_name)

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Сегодня", callback_data=f"classroom_today_{classroom_name}"),
        InlineKeyboardButton(text="Завтра", callback_data=f"classroom_tomorrow_{classroom_name}"),
        InlineKeyboardButton(text="Неделя", callback_data=f"classroom_week_{classroom_name}"),
    )
    builder.adjust(2, 1)

    await message.answer(
        f"Вы ищете аудиторию: <b>{classroom_name}</b>. Выберите период:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.clear()

#Обработчик выбора периода для аудитории
@router.callback_query(F.data.startswith('classroom_'))
async def process_classroom_period(callback: CallbackQuery):
    await callback.answer()
    try:
        _, period_type, classroom_name = callback.data.split('_', maxsplit=2)
        
        today = datetime.now().date()
        if period_type == 'today':
            dates = [today.strftime('%Y-%m-%d')]
            period_text = "на сегодня"
        elif period_type == 'tomorrow':
            dates = [(today + timedelta(days=1)).strftime('%Y-%m-%d')]
            period_text = "на завтра"
        else:  # week
            dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            period_text = "на неделю"

        all_groups = Config.GROUPS
        found_pairs = []
        
        # Сначала проверяем кэш
        cached_pairs = []
        need_fetch = []
        
        for date in dates:
            for group in all_groups:
                query_params = {"date": date, "group": group, "teacher": ""}
                cached_data = get_cached(query_params)
                if cached_data:
                    cached_pairs.extend(
                        pair for pair in cached_data 
                        if classroom_name.lower() in pair['class_name'].lower()
                    )
                else:
                    need_fetch.append(query_params)

        # Делаем batch-запрос для отсутствующих в кэше данных
        if need_fetch:
            async with APIClient() as client:
                # Используем batch-запрос для всех нужных данных
                batch_data = await client.fetch_batch_schedules(
                    date_list=list({p['date'] for p in need_fetch}),
                    group_list=list({p['group'] for p in need_fetch})
                )
                
                # Обрабатываем результаты
                for key, data in batch_data.items():
                    if data:
                        date, group = key.split('_')
                        query_params = {"date": date, "group": group, "teacher": ""}
                        save_to_db(data, query_params)
                        found_pairs.extend(
                            pair for pair in data 
                            if classroom_name.lower() in pair['class_name'].lower()
                        )

        # Объединяем результаты из кэша и новых запросов
        all_pairs = cached_pairs + found_pairs

        if all_pairs:
            schedule_text = format_classroom_schedule(all_pairs)
            response = f"<b>📅 Расписание аудитории {classroom_name} {period_text}:</b>\n\n{schedule_text}"
        else:
            response = f"✅ Аудитория <b>{classroom_name}</b> свободна {period_text}."

        await send_long_message(callback.message, response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in classroom schedule: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при получении расписания")

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

    today = datetime.now()
    day_display = {
        'today': 'на сегодня',
        'tomorrow': 'на завтра',
        'week': 'на неделю'
    }

    try:
        if day_type == 'week':
            # Оптимизированный запрос для недели
            dates = [(today + timedelta(days=day)).strftime('%Y-%m-%d') for day in range(7)]
            
            # Проверяем кэш
            cached_data = []
            need_fetch = []
            
            for date in dates:
                query_params = {'date': date, 'group': group_name, 'teacher': ''}
                if (data := get_cached(query_params)):
                    cached_data.extend(data)
                else:
                    need_fetch.append(date)
            
            # Делаем batch-запрос для отсутствующих дат
            if need_fetch:
                async with APIClient() as client:
                    batch_data = await client.fetch_batch_schedules(
                        date_list=need_fetch,
                        group_list=[group_name]
                    )
                    
                    for key, data in batch_data.items():
                        if data:
                            date = key.split('_')[0]
                            query_params = {'date': date, 'group': group_name, 'teacher': ''}
                            save_to_db(data, query_params)
                            cached_data.extend(data)
            
            schedule_text = format_schedule(cached_data) if cached_data else "Не удалось получить расписание"
        else:
            # Обработка для сегодня/завтра
            date_map = {
                'today': today.strftime('%Y-%m-%d'),
                'tomorrow': (today + timedelta(days=1)).strftime('%Y-%m-%d')
            }

            query_params = {
                'date': date_map[day_type],
                'group': group_name,
                'teacher': ''
            }

            if (cached_data := get_cached(query_params)):
                schedule_text = format_schedule(cached_data)
            else:
                async with APIClient() as client:
                    if (api_data := await client.fetch_schedule(query_params)):
                        save_to_db(api_data, query_params)
                        schedule_text = format_schedule(api_data)
                    else:
                        schedule_text = "Не удалось получить расписание"

        await callback.message.edit_text(
            f"📅 Расписание группы {group_name} {day_display[day_type]}:\n\n{schedule_text}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in schedule handler: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при получении расписания")