import asyncio
from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from bot.db.db_utils import (
    get_cached,
    save_to_db
)
from ..api.api_serv import fetch_schedule_from_api
from config import Config
from ..keyboards.keyboards import (
    main_keyboard,
    program_keyboard,
    courses_keyboard,
    groups_keyboard,
    day_selection_keyboard
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

router = Router()

class TeacherStates(StatesGroup):
    waiting_for_teacher_name = State()

class ClassroomStates(StatesGroup):
    waiting_for_classroom_name = State()

async def send_long_message(message: Message, text: str, **kwargs):
    """Отправляет длинное сообщение частями с поддержкой всех параметров message.answer()"""
    max_length = 4096  # Максимальная длина сообщения в Telegram
    
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

def format_schedule(schedule_data):
    if not schedule_data:
        return "Расписание не найдено"

    # Группируем по дням недели
    days = {}
    for item in schedule_data:
        day = item['weekday']
        if day not in days:
            days[day] = []
        days[day].append(item)

    # Сортируем дни по порядку недели
    week_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    sorted_days = sorted(days.items(), key=lambda x: week_order.index(x[0]) if x[0] in week_order else 7)

    result = []
    for day, pairs in sorted_days:
        day_schedule = f"<b>📌 {day.upper()}</b>\n"
        
        if not pairs:
            day_schedule += "    🎉 Пар нет\n"
        else:
            for pair in sorted(pairs, key=lambda x: x['pair_start_time']):
                day_schedule += (
                    f"    ⏰ {pair['pair_start_time']}-{pair['pair_end_time']}\n"
                    f"    📚 {pair['subject_name']} ({pair['pair_type']})\n"
                    f"    👨‍🏫 {pair.get('teacher', 'Преподаватель не указан')}\n"
                    f"    🚪 {pair.get('class_name', 'Аудитория не указана')}\n"
                )
                
                # Добавляем информацию о неделе (верхняя/нижняя), если есть
                if pair.get('week_type'):
                    day_schedule += f"    🔄 Неделя: {pair['week_type']}\n"
                
                day_schedule += "\n"
        
        result.append(day_schedule)

    return "\n".join(result) if result else "На этот период пар нет"

def format_teacher_schedule(found_pairs: list) -> str:
    """Форматирует расписание преподавателя в читаемый вид"""
    if not found_pairs:
        return "Пары не найдены"
    
    # Группируем по дням недели
    days = {}
    for pair in found_pairs:
        day = pair['weekday']
        if day not in days:
            days[day] = []
        days[day].append(pair)
    
    # Сортируем дни по порядку недели
    week_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    sorted_days = sorted(days.items(), key=lambda x: week_order.index(x[0]) if x[0] in week_order else 7)
    
    result = []
    for day, pairs in sorted_days:
        day_header = f"<b>📌 {day.upper()}</b>\n"
        day_schedule = []
        
        for pair in sorted(pairs, key=lambda x: x['pair_start_time']):
            # Форматируем время (заменяем точки на двоеточия при необходимости)
            start_time = pair['pair_start_time'].replace('.', ':')
            end_time = pair['pair_end_time'].replace('.', ':')
            
            pair_info = [
                f"    ⏰ {start_time}-{end_time}",
                f"    📚 {pair['subject_name']} ({pair['pair_type']})",
                f"    🚪 Ауд. {pair['class_name']}",
                f"    👥 Группа: {pair['group_name']}"
            ]
            
            # Добавляем информацию о неделе, если есть
            if pair.get('week_type'):
                pair_info.append(f"    🔄 {pair['week_type'].capitalize()} неделя")
            
            day_schedule.append("\n".join(pair_info))
        
        if day_schedule:
            result.append(day_header + "\n".join(day_schedule))
    
    return "\n\n".join(result) if result else "Пары не найдены"

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

# Обработчик кнопки "Преподаватель"
@router.callback_query(F.data == 'teacher')
async def handle_teacher_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки поиска по преподавателю"""
    await callback.message.answer(
        "🔍 Введите фамилию преподавателя (например: <i>Ильин</i> или <i>Ильин Б.П.</i>):",
        parse_mode="HTML"
    )
    await state.set_state(TeacherStates.waiting_for_teacher_name)
    await callback.answer()

@router.message(TeacherStates.waiting_for_teacher_name)
async def process_teacher_name(message: Message, state: FSMContext):
    """Обработчик ввода имени преподавателя и поиска расписания"""
    teacher_name = message.text.strip()
    if len(teacher_name) < 3:
        await message.answer("❌ Слишком короткий запрос. Введите фамилию преподавателя (минимум 3 символа).")
        return
    
    # Получаем текущую дату и дату через неделю
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    # Здесь должен быть реальный список всех групп из вашей БД
    # Для примера используем несколько групп
    all_groups = ['02121-ДБ', '02122-ДБ', '02123-ДБ', '02141-ДБ', '02161-ДБ', '02162-ДБ', '02171-ДБ', '02172-ДБ', '02181-ДБ','02221-ДБ', '02222-ДБ', '02223-ДБ', '02241-ДБ', '02261-ДБ', '02262-ДБ', '02271-ДБ', '02272-ДБ', '02281-ДБ','02321-ДБ', '02322-ДБ', '02323-ДБ', '02341-ДБ', '02361-ДБ', '02362-ДБ', '02371-ДБ', '02372-ДБ', '02381-ДБ','02421-ДБ', '02422-ДБ', '02423-ДБ', '02441-ДБ', '02461-ДБ', '02471-ДБ', '02481-ДБ','02121-ДМ', '02123-ДМ', '02161-ДМ', '02171-ДМ','02221-ДМ', '02222-ДМ', '02261-ДМ', '02271-ДМ']
    
    found_pairs = []
    
    # Ищем пары преподавателя во всех группах на все дни недели
    for date in dates:
        for group in all_groups:
            query_params = {
                "date": date,
                "group": group,
                "teacher": ""
            }
            
            # Проверяем кэш
            cached_data = get_cached(query_params)
            if cached_data:
                schedule_data = cached_data
            else:
                schedule_data = await fetch_schedule_from_api(query_params)
                if schedule_data:
                    save_to_db(schedule_data, query_params)
            
            # Фильтруем пары по преподавателю (ищем вхождение в ФИО)
            if schedule_data:
                for pair in schedule_data:
                    if (teacher_name.lower() in pair['teacher'].lower() or 
                        teacher_name.lower() in pair['lastname'].lower()):
                        found_pairs.append(pair)
    
    # Форматируем результат
    if found_pairs:
        schedule_text = format_teacher_schedule(found_pairs)
        response = (
            f"<b>📅 Расписание преподавателя {teacher_name.capitalize()} на неделю:</b>\n\n"
            f"{schedule_text}\n\n"
        )
    else:
        response = f"❌ Преподаватель <b>{teacher_name.capitalize()}</b> не найден в расписании на текущую неделю."
    
    await send_long_message(message, response, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == 'classroom')
async def handle_classroom_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки поиска по аудитории"""
    await callback.message.answer(
        "🔍 Введите номер аудитории (например: <i>113-3</i> или <i>312а</i>):",
        parse_mode="HTML"
    )
    await state.set_state(ClassroomStates.waiting_for_classroom_name)
    await callback.answer()

def format_classroom_schedule(found_pairs: list) -> str:
    """Форматирует расписание аудитории в читаемый вид"""
    if not found_pairs:
        return "Аудитория свободна"
    
    # Группируем по дням недели
    days = {}
    for pair in found_pairs:
        day = pair['weekday']
        if day not in days:
            days[day] = []
        days[day].append(pair)
    
    # Сортируем дни по порядку недели
    week_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    sorted_days = sorted(days.items(), key=lambda x: week_order.index(x[0]) if x[0] in week_order else 7)
    
    result = []
    for day, pairs in sorted_days:
        day_header = f"<b>📌 {day.upper()}</b>\n"
        day_schedule = []
        
        for pair in sorted(pairs, key=lambda x: x['pair_start_time']):
            # Форматируем время (заменяем точки на двоеточия при необходимости)
            start_time = pair['pair_start_time'].replace('.', ':')
            end_time = pair['pair_end_time'].replace('.', ':')
            
            pair_info = [
                f"    ⏰ {start_time}-{end_time}",
                f"    📚 {pair['subject_name']} ({pair['pair_type']})",
                f"    👨‍🏫 {pair['teacher']}",
                f"    👥 Группа: {pair['group_name']}"
            ]
            
            # Добавляем информацию о неделе, если есть
            if pair.get('week_type'):
                pair_info.append(f"    🔄 {pair['week_type'].capitalize()} неделя")
            
            day_schedule.append("\n".join(pair_info))
        
        if day_schedule:
            result.append(day_header + "\n".join(day_schedule))
    
    return "\n\n".join(result) if result else "Аудитория свободна"

@router.message(ClassroomStates.waiting_for_classroom_name)
async def process_classroom_name(message: Message, state: FSMContext):
    """Обработчик ввода номера аудитории и поиска расписания"""
    classroom_name = message.text.strip().upper()
    if len(classroom_name) < 2:
        await message.answer("❌ Слишком короткий запрос. Введите номер аудитории (минимум 2 символа).")
        return
    
    # Получаем текущую дату и дату через неделю
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    all_groups = ['02121-ДБ', '02122-ДБ', '02123-ДБ', '02141-ДБ', '02161-ДБ', '02162-ДБ', '02171-ДБ', '02172-ДБ', '02181-ДБ','02221-ДБ', '02222-ДБ', '02223-ДБ', '02241-ДБ', '02261-ДБ', '02262-ДБ', '02271-ДБ', '02272-ДБ', '02281-ДБ','02321-ДБ', '02322-ДБ', '02323-ДБ', '02341-ДБ', '02361-ДБ', '02362-ДБ', '02371-ДБ', '02372-ДБ', '02381-ДБ','02421-ДБ', '02422-ДБ', '02423-ДБ', '02441-ДБ', '02461-ДБ', '02471-ДБ', '02481-ДБ','02121-ДМ', '02123-ДМ', '02161-ДМ', '02171-ДМ','02221-ДМ', '02222-ДМ', '02261-ДМ', '02271-ДМ']
    
    found_pairs = []
    
    # Ищем пары в указанной аудитории во всех группах на все дни недели
    for date in dates:
        for group in all_groups:
            query_params = {
                "date": date,
                "group": group,
                "teacher": ""
            }
            
            # Проверяем кэш
            cached_data = get_cached(query_params)
            if cached_data:
                schedule_data = cached_data
            else:
                schedule_data = await fetch_schedule_from_api(query_params)
                if schedule_data:
                    save_to_db(schedule_data, query_params)
            
            # Фильтруем пары по аудитории
            if schedule_data:
                for pair in schedule_data:
                    if classroom_name.lower() in pair['class_name'].lower():
                        found_pairs.append(pair)
    
    # Форматируем результат
    if found_pairs:
        schedule_text = format_classroom_schedule(found_pairs)
        response = (
            f"<b>📅 Расписание аудитории {classroom_name.upper()} на неделю:</b>\n\n"
            f"{schedule_text}\n\n"
            f"<i>ℹ️ Данные актуальны на {today.strftime('%d.%m.%Y')}</i>"
        )
    else:
        response = f"✅ Аудитория <b>{classroom_name.upper()}</b> свободна на текущую неделю."
    
    await send_long_message(message, response, parse_mode="HTML")
    await state.clear()

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
    
    if day_type == 'week':
        # Собираем расписание на всю неделю
        week_schedule = []
        for day in range(7):  # 7 дней недели
            current_date = (today + timedelta(days=day)).strftime('%Y-%m-%d')
            query_params = {
                'date': current_date,
                'group': group_name,
                'teacher': ''
            }
            
            # Проверяем кэш для каждого дня
            cached_data = get_cached(query_params)
            if cached_data:
                week_schedule.extend(cached_data)
            else:
                api_data = await fetch_schedule_from_api(query_params)
                if api_data:
                    save_to_db(api_data, query_params)
                    week_schedule.extend(api_data)
        
        schedule_text = format_schedule(week_schedule)
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

        if not schedule_text:
            schedule_text = "Не удалось получить расписание. Попробуйте позже."

    await callback.message.edit_text(
        f"📅 Расписание группы {group_name} {day_display[day_type]}:\n\n{schedule_text}",
        parse_mode="HTML"
    )
