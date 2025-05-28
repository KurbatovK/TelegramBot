import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        group_id INTEGER,
        group_name TEXT,
        weekday TEXT,
        pair_start_time TEXT,
        pair_end_time TEXT,
        subject_name TEXT,
        pair_type TEXT,
        teacher_id INTEGER,
        teacher TEXT,
        lastname TEXT,
        firstname TEXT,
        patronymic TEXT,
        class_name TEXT,
        week_type TEXT,
        begin_date_pairs TEXT,
        end_date_pairs TEXT,
        query_date TEXT,
        query_group TEXT,
        query_teacher TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Индексы для ускорения поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_query ON schedule (query_date, query_group, query_teacher)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_teacher ON schedule (teacher)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_group ON schedule (group_name)')
    
    conn.commit()
    conn.close()

init_db()