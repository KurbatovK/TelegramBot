from aiogram.fsm.state import State, StatesGroup

class TeacherStates(StatesGroup):
    waiting_for_teacher_name = State()
    waiting_for_period = State()
    waiting_for_custom_date = State()
    waiting_for_teacher_action = State()

class ClassroomStates(StatesGroup):
    waiting_for_classroom_name = State()
    waiting_for_period = State()
    waiting_for_custom_date = State()

class GroupStates(StatesGroup):
    waiting_for_custom_date = State()