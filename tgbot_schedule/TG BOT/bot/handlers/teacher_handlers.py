from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from .base_handlers import BaseHandler
from .states import TeacherStates
from datetime import timedelta, datetime
from bot.api.api_serv import APIClient
from config import Config
import logging
from bot.keyboards.keyboards import teachers_action_keyboard


logger = logging.getLogger(__name__)

class TeacherHandlers(BaseHandler):

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'teacher')
    async def handle_teacher_search(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.message.answer(
            "👨‍🏫 Выберите действие:",
            reply_markup=teachers_action_keyboard()
        )
        await state.set_state(TeacherStates.waiting_for_teacher_action)
        await callback.answer()
    
    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'show_all_teachers', TeacherStates.waiting_for_teacher_action)
    async def show_all_teachers(callback: CallbackQuery, state: FSMContext) -> None:
        try:
            async with APIClient() as client:
                teachers = await client.fetch_all_teachers()
            
            if teachers:
                # Разбиваем список на части, чтобы не превысить лимит сообщения
                chunk_size = 30
                teacher_chunks = [teachers[i:i + chunk_size] for i in range(0, len(teachers), chunk_size)]
                
                for chunk in teacher_chunks:
                    teachers_list = "\n".join([f"• {t['full_name']}" for t in chunk])
                    await callback.message.answer(
                        f"👨‍🏫 <b>Список преподавателей:</b>\n\n{teachers_list}",
                        parse_mode="HTML"
                    )
                
                await callback.message.answer(
                    "🔍 Теперь вы можете ввести фамилию преподавателя:",
                    reply_markup=teachers_action_keyboard()
                )
            else:
                await callback.message.answer(
                    "❌ Не удалось загрузить список преподавателей",
                    reply_markup=teachers_action_keyboard()
                )
            
            await state.set_state(TeacherStates.waiting_for_teacher_name)
        except Exception as e:
            logger.error(f"Error fetching teachers list: {e}", exc_info=True)
            await callback.message.answer(
                "❌ Ошибка при получении списка преподавателей",
                reply_markup=teachers_action_keyboard()
            )
        finally:
            await callback.answer()

    @staticmethod
    @BaseHandler.router.callback_query(F.data == 'enter_teacher_name', TeacherStates.waiting_for_teacher_action)
    async def ask_for_teacher_name(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.message.answer(
            "🔍 Введите фамилию преподавателя (например: <i>Ильин</i> или <i>Ильин Б.П.</i>):",
            parse_mode="HTML"
        )
        await state.set_state(TeacherStates.waiting_for_teacher_name)
        await callback.answer()

    @staticmethod
    @BaseHandler.router.message(TeacherStates.waiting_for_teacher_name)
    async def process_teacher_name(message: Message, state: FSMContext) -> None:
        teacher_name = message.text.strip()
        if len(teacher_name) < 3:
            await message.answer("❌ Слишком короткий запрос. Введите фамилию преподавателя (минимум 3 символа).")
            return

        await BaseHandler.ask_for_period(
            message=message,
            entity_name=teacher_name,
            state=state,
            entity_type='teacher'
        )

    @staticmethod
    @BaseHandler.router.callback_query(F.data.startswith('teacher_'))
    async def process_teacher_period(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        
        try:
            _, period_type, teacher_name = callback.data.split('_', maxsplit=2)
            
            if period_type == 'custom':
                await state.set_state(TeacherStates.waiting_for_custom_date)
                await state.update_data(teacher_name=teacher_name)
                await callback.message.answer(
                    "📅 Введите дату в формате ДД.ММ.ГГГГ (например, 15.09.2023):"
                )
                return
            
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
                schedule_text = TeacherHandlers.format_teacher_schedule(found_pairs)
                response = f"<b>📅 Расписание преподавателя {teacher_name} {period_text}:</b>\n\n{schedule_text}"
            else:
                response = f"❌ Преподаватель {teacher_name} не найден в расписании {period_text}."

            await BaseHandler.send_long_message(callback.message, response, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error in teacher schedule: {e}", exc_info=True)
            await callback.message.answer("❌ Ошибка при получении расписания")

    @staticmethod
    @BaseHandler.router.message(TeacherStates.waiting_for_custom_date)
    async def process_teacher_custom_date(message: Message, state: FSMContext) -> None:
        await BaseHandler.process_custom_date(
            message=message,
            state=state,
            entity_type='teacher',
            formatter=TeacherHandlers.format_teacher_schedule,
            not_found_msg=f"❌ Преподаватель не найден в расписании на указанную дату."
        )

    @staticmethod
    def format_teacher_schedule(found_pairs: list) -> str:
        def formatter(pair):
            return [
                f"    ⏰ {pair['pair_start_time'].replace('.', ':')}-{pair['pair_end_time'].replace('.', ':')}",
                f"    📚 {pair['subject_name']} ({pair['pair_type']})",
                f"    🚪 Ауд. {pair['class_name']}",
                f"    👥 Группа: {pair['group_name']}"
            ]
        
        return BaseHandler._base_schedule_formatter(
            found_pairs,
            title="Расписание преподавателя",
            pair_formatter=formatter,
            empty_message="Пары не найдены"
        )
    
