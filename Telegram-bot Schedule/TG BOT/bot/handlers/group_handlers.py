from bot.db.db_utils import save_to_db, get_cached
from datetime import timedelta, datetime
from bot.api.api_serv import APIClient
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from .base_handlers import BaseHandler
from .states import GroupStates
from ..keyboards.keyboards import day_selection_keyboard
import logging

logger = logging.getLogger(__name__)

class GroupHandlers(BaseHandler):
    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('day_custom_'))
    async def handle_custom_date_group(callback: CallbackQuery, state: FSMContext) -> None:
        _, _, group_name, program_year = callback.data.split('_', 3)
        await state.set_state(GroupStates.waiting_for_custom_date)
        await state.update_data(group_name=group_name, program_year=program_year)
        await callback.message.answer("📅 Введите дату в формате ДД.ММ.ГГГГ (например, 15.09.2023):")
        await callback.answer()

    @staticmethod
    @BaseHandler.router.message(GroupStates.waiting_for_custom_date)
    async def process_group_custom_date(message: Message, state: FSMContext) -> None:
        await GroupHandlers.process_custom_date(
            message=message,
            state=state,
            entity_type='group',
            formatter=GroupHandlers.format_schedule,
            not_found_msg="Не удалось получить расписание"
        )

    @staticmethod
    def format_schedule(schedule_data: list) -> str:
        def formatter(pair):
            return [
                f"    ⏰ {pair['pair_start_time']}-{pair['pair_end_time']}",
                f"    📚 {pair['subject_name']} ({pair['pair_type']})",
                f"    👨‍🏫 {pair.get('teacher', 'Преподаватель не указан')}",
                f"    🚪 {pair.get('class_name', 'Аудитория не указана')}"
            ]
        
        return BaseHandler._base_schedule_formatter(
            schedule_data,
            title="Расписание группы",
            pair_formatter=formatter,
            empty_message="На этот период пар нет"
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('group_'))
    async def select_day(callback: CallbackQuery) -> None:
        await callback.answer()
        _, group_name, program_year = callback.data.split('_', 2)
        await callback.message.edit_text(
            f'Выбери день для группы {group_name}:',
            reply_markup=day_selection_keyboard(group_name, program_year)
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('day_'))
    async def show_schedule(callback: CallbackQuery) -> None:
        await callback.answer()
        _, day_type, group_name, program_year = callback.data.split('_', 3)

        day_display = {
            'today': 'на сегодня',
            'tomorrow': 'на завтра',
            'week': 'на неделю'
        }

        try:
            today = datetime.now()
            if day_type == 'week':
                dates = [(today + timedelta(days=day)).strftime('%Y-%m-%d') for day in range(7)]
                
                cached_data = []
                need_fetch = []
                
                for date in dates:
                    query_params = {'date': date, 'group': group_name, 'teacher': ''}
                    if (data := get_cached(query_params)):
                        cached_data.extend(data)
                    else:
                        need_fetch.append(date)
                
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
                
                schedule_text = GroupHandlers.format_schedule(cached_data) if cached_data else "Не удалось получить расписание"
            else:
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
                    schedule_text = GroupHandlers.format_schedule(cached_data)
                else:
                    async with APIClient() as client:
                        if (api_data := await client.fetch_schedule(query_params)):
                            save_to_db(api_data, query_params)
                            schedule_text = GroupHandlers.format_schedule(api_data)
                        else:
                            schedule_text = "Не удалось получить расписание"

            await callback.message.edit_text(
                f"📅 Расписание группы {group_name} {day_display[day_type]}:\n\n{schedule_text}",
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Error in schedule handler: {e}", exc_info=True)
            await callback.message.answer("❌ Ошибка при получении расписания")