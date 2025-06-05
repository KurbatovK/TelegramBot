from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text='👨‍🏫 Поиск преподавателя', callback_data='teacher'),
        InlineKeyboardButton(text='📅 Твоё расписание', callback_data='schedule'),
        InlineKeyboardButton(text='🔍 Поиск по аудитории', callback_data='classroom'),
        InlineKeyboardButton(text='ℹ️ Информация', callback_data="information")
    )
    builder.adjust(2, 2)
    return builder.as_markup()

def program_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text='Бакалавриат', callback_data='bachelor'),
        InlineKeyboardButton(text='Магистратура', callback_data='master'),
        InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    )
    builder.adjust(2, 1)
    return builder.as_markup()

def courses_keyboard(program_type):
    builder = InlineKeyboardBuilder()

    if program_type == 'bachelor':
        for year in range(1, 5):
            builder.button(text=f'{year} курс', callback_data=f'bachelor_{year}')
    else:
        for year in range(1, 3):
            builder.button(text=f'{year} курс', callback_data=f'master_{year}')

    builder.button(text='Назад', callback_data='back_to_programs')
    builder.adjust(2, 1)
    return builder.as_markup()

def groups_keyboard(program_year):
    builder = InlineKeyboardBuilder()

    groups_data = {
        'bachelor_1': ['02121-ДБ', '02122-ДБ', '02123-ДБ', '02141-ДБ', '02161-ДБ', '02162-ДБ', '02171-ДБ', '02172-ДБ', '02181-ДБ'],
        'bachelor_2': ['02221-ДБ', '02222-ДБ', '02223-ДБ', '02241-ДБ', '02261-ДБ', '02262-ДБ', '02271-ДБ', '02272-ДБ', '02281-ДБ'],
        'bachelor_3': ['02321-ДБ', '02322-ДБ', '02323-ДБ', '02341-ДБ', '02361-ДБ', '02362-ДБ', '02371-ДБ', '02372-ДБ', '02381-ДБ'],
        'bachelor_4': ['02421-ДБ', '02422-ДБ', '02423-ДБ', '02441-ДБ', '02461-ДБ', '02471-ДБ', '02481-ДБ'],
        'master_1': ['02121-ДМ', '02123-ДМ', '02161-ДМ', '02171-ДМ'],
        'master_2': ['02221-ДМ', '02222-ДМ', '02261-ДМ', '02271-ДМ']
    }

    current_groups = groups_data.get(program_year, [])

    for group in current_groups:
        builder.button(text=group, callback_data=f"group_{group}_{program_year}")

    builder.button(text='Назад', callback_data=f'back_to_{program_year.split("_")[0]}')
    builder.adjust(2)
    return builder.as_markup()

def day_selection_keyboard(group_name, program_year):
    builder = InlineKeyboardBuilder()

    builder.button(text='Сегодня', callback_data=f'day_today_{group_name}_{program_year}')
    builder.button(text='Завтра', callback_data=f'day_tomorrow_{group_name}_{program_year}')
    builder.button(text='Вся неделя', callback_data=f'day_week_{group_name}_{program_year}')
    builder.button(text='Другая дата', callback_data=f'day_custom_{group_name}_{program_year}')

    if program_year.startswith('bachelor_'):
        back_callback = 'back_to_bachelor'
    elif program_year.startswith('master_'):
        back_callback = 'back_to_master'
    else:
        back_callback = 'back_to_programs'
    
    builder.button(text='Назад к группам', callback_data=back_callback)

    builder.adjust(2, 2)
    return builder.as_markup()

def get_period_keyboard(prefix: str, entity: str):
    """Универсальная клавиатура для выбора периода"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Сегодня", callback_data=f"{prefix}_today_{entity}"),
        InlineKeyboardButton(text="Завтра", callback_data=f"{prefix}_tomorrow_{entity}"),
        InlineKeyboardButton(text="Неделя", callback_data=f"{prefix}_week_{entity}"),
        InlineKeyboardButton(text="Другая дата", callback_data=f"{prefix}_custom_{entity}"),
    )
    builder.adjust(2, 2)
    return builder.as_markup()
