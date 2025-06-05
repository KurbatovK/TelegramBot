import sqlite3
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

def save_to_db(data: list, query_params: dict):
    if not data:
        logger.warning("Попытка сохранить пустые данные в БД")
        return
    
    if not data or not all(item.get('id') for item in data):
        logger.warning("Получены неверные данные, не сохраняются в БД")
        return

    try:
        conn = sqlite3.connect('schedule.db')
        cursor = conn.cursor()
        
        #INSERT OR REPLACE для избежания конфликтов
        for item in data:
            cursor.execute('''
            INSERT OR REPLACE INTO schedule (
                id, group_id, group_name, weekday, pair_start_time, pair_end_time,
                subject_name, pair_type, teacher_id, teacher, lastname, firstname,
                patronymic, class_name, week_type, begin_date_pairs, end_date_pairs,
                query_date, query_group, query_teacher, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('id'), item.get('group_id'), item.get('group_name'), 
                item.get('weekday'), item.get('pair_start_time'), item.get('pair_end_time'),
                item.get('subject_name'), item.get('pair_type'), item.get('teacher_id'),
                item.get('teacher'), item.get('lastname'), item.get('firstname'),
                item.get('patronymic'), item.get('class_name'), item.get('week_type'),
                item.get('begin_date_pairs'), item.get('end_date_pairs'),
                query_params['date'], query_params['group'], query_params['teacher'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        conn.commit()
        logger.info(f"Сохраненные {len(data)} записи в БД для {query_params}")
        
    except sqlite3.Error as e:
        logger.error(f"db ошибка: {e}")
        raise  # Пробрасываем исключение дальше
    finally:
        if conn:
            conn.close()

def get_cached(query_params: dict):
    try:
        conn = sqlite3.connect('schedule.db')
        cursor = conn.cursor()
        
        # Получаем данные и время последнего обновления
        cursor.execute('''
        SELECT *, last_updated FROM schedule 
        WHERE query_date = ? AND query_group = ? AND query_teacher = ?
        ''', (query_params['date'], query_params['group'], query_params['teacher']))
        
        rows = cursor.fetchall()
        if not rows:
            logger.debug("Кэшированные данные не найдены.")
            return None
            
        # Проверяем актуальность данных
        last_updated_str = rows[0][-1]  # last_updated - последний столбец
        last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d %H:%M:%S')
        
        if (datetime.now() - last_updated).total_seconds() > Config.CACHE_TTL:
            logger.debug("Срок действия кэшированных данных истек")
            return None
            
        # Форматируем результат
        columns = [column[0] for column in cursor.description]
        results = []
        for row in rows:
            results.append(dict(zip(columns[:-1], row[:-1])))  # Исключаем last_updated
            
        logger.debug(f"Returning {len(results)} cached records")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()