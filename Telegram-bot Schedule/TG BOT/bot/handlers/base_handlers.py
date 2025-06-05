from typing import Callable
from datetime import datetime
import asyncio
import logging
from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from ..api.api_serv import APIClient
from config import Config
from bot.db.db_utils import get_cached, save_to_db

logger = logging.getLogger(__name__)

class BaseHandler:
    router = Router()
    
    @staticmethod
    async def send_long_message(message: Message, text: str, **kwargs) -> None:
        max_length = 4096
        if len(text) <= max_length:
            await message.answer(text, **kwargs)
            return

        parts = []
        while text:
            part = text[:max_length]
            last_newline = part.rfind('\n')
            if last_newline > 0:
                part = part[:last_newline]
                remaining = text[last_newline+1:]
            else:
                remaining = text[max_length:]
            parts.append(part)
            text = remaining

        for part in parts:
            await message.answer(part, **kwargs)
            await asyncio.sleep(0.5)

    @staticmethod
    def _base_schedule_formatter(
        items: list,
        title: str,
        pair_formatter: Callable,
        empty_message: str = "Данные не найдены"
    ) -> str:
        if not items:
            return empty_message

        days = {}
        for item in items:
            day = item['weekday']
            days.setdefault(day, []).append(item)

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
                day_schedule_with_seps = []
                for i, pair in enumerate(day_schedule):
                    day_schedule_with_seps.append(pair)
                    if i < len(day_schedule) - 1:
                        day_schedule_with_seps.append("    ───────────────")
                
                result.append(day_header + "\n".join(day_schedule_with_seps))

        return "\n\n".join(result) if result else empty_message

    @staticmethod
    async def process_custom_date(
        message: Message,
        state: FSMContext,
        entity_type: str,
        formatter: Callable,
        not_found_msg: str
    ) -> None:
        try:
            date_obj = datetime.strptime(message.text, '%d.%m.%Y').date()
            date_str = date_obj.strftime('%Y-%m-%d')
            
            data = await state.get_data()
            entity_name = data[f'{entity_type}_name']
            
            all_groups = Config.GROUPS
            found_pairs = []
            
            if entity_type == 'group':
                query_params = {'date': date_str, 'group': entity_name, 'teacher': ''}
                if (cached_data := get_cached(query_params)):
                    schedule_text = formatter(cached_data)
                else:
                    async with APIClient() as client:
                        if (api_data := await client.fetch_schedule(query_params)):
                            save_to_db(api_data, query_params)
                            schedule_text = formatter(api_data)
                        else:
                            schedule_text = not_found_msg
                
                await message.answer(
                    f"📅 Расписание группы {entity_name} на {message.text}:\n\n{schedule_text}",
                    parse_mode="HTML"
                )
            else:
                async with APIClient() as client:
                    batch_data = await client.fetch_batch_schedules(
                        date_list=[date_str],
                        group_list=all_groups
                    )
                
                for data in batch_data.values():
                    if data:
                        for pair in data:
                            if (entity_type == 'teacher' and 
                                (entity_name.lower() in pair['teacher'].lower() or
                                 entity_name.lower() in pair.get('lastname', '').lower())):
                                found_pairs.append(pair)
                            elif (entity_type == 'classroom' and 
                                  entity_name.lower() in pair['class_name'].lower()):
                                found_pairs.append(pair)

                if found_pairs:
                    schedule_text = formatter(found_pairs)
                    response = (f"<b>📅 Расписание {'преподавателя' if entity_type == 'teacher' else 'аудитории'} "
                              f"{entity_name} на {message.text}:</b>\n\n{schedule_text}")
                else:
                    response = not_found_msg

                await BaseHandler.send_long_message(message, response, parse_mode="HTML")
            
            await state.clear()
            
        except ValueError:
            await message.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
        except Exception as e:
            logger.error(f"Error in {entity_type} custom date handler: {e}", exc_info=True)
            await message.answer("❌ Ошибка при получении расписания")
            await state.clear()

    @staticmethod
    async def ask_for_period(
        message: Message,
        entity_name: str,
        state: FSMContext,
        entity_type: str
    ) -> None:
        from ..keyboards.keyboards import get_period_keyboard
        
        entity_display = {
            'teacher': 'преподавателя',
            'classroom': 'аудитории',
            'group': 'группы'
        }.get(entity_type, '')
        
        await message.answer(
            f"Вы ищете {entity_display}: <b>{entity_name}</b>. Выберите период:",
            reply_markup=get_period_keyboard(entity_type, entity_name),
            parse_mode="HTML"
        )
        await state.clear()