import sqlite3
from datetime import datetime
from config import Config

def save_to_db(data: list, query_params: dict):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    DELETE FROM schedule 
    WHERE query_date = ? AND query_group = ? AND query_teacher = ?
    ''', (query_params['date'], query_params['group'], query_params['teacher']))
    
    for item in data:
        cursor.execute('''
        INSERT INTO schedule (
            id, group_id, group_name, weekday, pair_start_time, pair_end_time,
            subject_name, pair_type, teacher_id, teacher, lastname, firstname,
            patronymic, class_name, week_type, begin_date_pairs, end_date_pairs,
            query_date, query_group, query_teacher
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['id'], item['group_id'], item['group_name'], item['weekday'],
            item['pair_start_time'], item['pair_end_time'], item['subject_name'],
            item['pair_type'], item['teacher_id'], item['teacher'], item['lastname'],
            item['firstname'], item['patronymic'], item['class_name'], item['week_type'],
            item['begin_date_pairs'], item['end_date_pairs'], query_params['date'], 
            query_params['group'], query_params['teacher']
        ))
    
    conn.commit()
    conn.close()

def get_cached(query_params: dict):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM schedule 
    WHERE query_date = ? AND query_group = ? AND query_teacher = ?
    ORDER BY last_updated DESC
    LIMIT 1
    ''', (query_params['date'], query_params['group'], query_params['teacher']))
    
    cached_data = cursor.fetchone()
    
    if cached_data:
        last_updated = datetime.strptime(cached_data[-1], '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - last_updated).total_seconds() < Config.CACHE_TTL:
            cursor.execute('''
            SELECT * FROM schedule 
            WHERE query_date = ? AND query_group = ? AND query_teacher = ?
            ''', (query_params['date'], query_params['group'], query_params['teacher']))
            
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return results
    
    conn.close()
    return None