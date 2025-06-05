from datetime import timedelta, datetime
from config import Config
from bot.api.api_serv import APIClient
from bot.db.db_utils import save_to_db, get_cached
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from .base_handlers import BaseHandler
from .states import ClassroomStates
import logging

logger = logging.getLogger(__name__)

class ClassroomHandlers(BaseHandler):
    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'classroom')
    async def handle_classroom_search(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.message.answer(
            "🔍 Введите номер аудитории (например: <i>113-3</i> или <i>312а</i>):",
            parse_mode="HTML"
        )
        await state.set_state(ClassroomStates.waiting_for_classroom_name)
        await callback.answer()

    @staticmethod
    @BaseHandler.router.message(ClassroomStates.waiting_for_classroom_name)
    async def process_classroom_name(message: Message, state: FSMContext) -> None:
        classroom_name = message.text.strip().upper()
        
        if len(classroom_name) < 2:
            await message.answer("❌ Слишком короткий запрос. Введите номер аудитории (минимум 2 символа).")
            return

        await state.update_data(classroom_name=classroom_name)
        await BaseHandler.ask_for_period(
            message=message,
            entity_name=classroom_name,
            state=state,
            entity_type='classroom'
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('classroom_'))
    async def process_classroom_period(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        try:
            _, period_type, classroom_name = callback.data.split('_', maxsplit=2)

            if period_type == 'custom':
                await state.set_state(ClassroomStates.waiting_for_custom_date)
                await state.update_data(classroom_name=classroom_name)
                await callback.message.answer(
                    "📅 Введите дату в формате ДД.ММ.ГГГГ (например, 15.09.2023):"
                )
                return
            
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
            
            # Проверяем кэш
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

            # Делаем batch-запрос для отсутствующих данных
            if need_fetch:
                async with APIClient() as client:
                    batch_data = await client.fetch_batch_schedules(
                        date_list=list({p['date'] for p in need_fetch}),
                        group_list=list({p['group'] for p in need_fetch})
                    )
                    
                    for key, data in batch_data.items():
                        if data:
                            date, group = key.split('_')
                            query_params = {"date": date, "group": group, "teacher": ""}
                            save_to_db(data, query_params)
                            found_pairs.extend(
                                pair for pair in data 
                                if classroom_name.lower() in pair['class_name'].lower()
                            )

            # Объединяем результаты
            all_pairs = cached_pairs + found_pairs

            if all_pairs:
                schedule_text = ClassroomHandlers.format_classroom_schedule(all_pairs)
                response = f"<b>📅 Расписание аудитории {classroom_name} {period_text}:</b>\n\n{schedule_text}"
            else:
                response = f"✅ Аудитория <b>{classroom_name}</b> свободна {period_text}."

            await BaseHandler.send_long_message(callback.message, response, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error in classroom schedule: {e}", exc_info=True)
            await callback.message.answer("❌ Ошибка при получении расписания")

    @staticmethod
    @BaseHandler.router.message(ClassroomStates.waiting_for_custom_date)
    async def process_classroom_custom_date(message: Message, state: FSMContext) -> None:
        await BaseHandler.process_custom_date(
            message=message,
            state=state,
            entity_type='classroom',
            formatter=ClassroomHandlers.format_classroom_schedule,
            not_found_msg=f"✅ Аудитория свободна на указанную дату."
        )

    @staticmethod
    def format_classroom_schedule(found_pairs: list) -> str:
        def formatter(pair):
            return [
                f"    ⏰ {pair['pair_start_time'].replace('.', ':')}-{pair['pair_end_time'].replace('.', ':')}",
                f"    📚 {pair['subject_name']} ({pair['pair_type']})",
                f"    👨‍🏫 {pair['teacher']}",
                f"    👥 Группа: {pair['group_name']}"
            ]
        
        return BaseHandler._base_schedule_formatter(
            found_pairs,
            title="Расписание аудитории",
            pair_formatter=formatter,
            empty_message="Аудитория свободна"
        )