from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text='Расписание преподавателя', callback_data='teacher'),
        InlineKeyboardButton(text='Твоё расписание', callback_data='schedule'),
        InlineKeyboardButton(text='Информация', callback_data="information")
    )
    builder.adjust(2, 1)
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
    program = program_year.split('_')[0]  # 'bachelor' или 'master'

    # Здесь группы
    builder.button(text="Пример группы", callback_data="group_1")

    builder.button(text='Назад', callback_data=f'back_to_{program}')
    builder.adjust(1)
    return builder.as_markup()
