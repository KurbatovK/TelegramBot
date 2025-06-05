import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class APIClient:
    """Клиент для работы с API расписания с поддержкой async with"""
    
    def __init__(self):
        self.session = None
        self.last_request_time = None
        self.request_interval = timedelta(seconds=1)
        self.semaphore = asyncio.Semaphore(5)  # Ограничение параллельных запросов

    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Выход из контекстного менеджера"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def fetch_schedule(self, query_params: dict) -> list | None:
        """Получение расписания с обработкой параметров"""
        if not all(key in query_params for key in ('date', 'group')):
            logger.error("Missing required query parameters")
            return None

        payload = {
            "date": query_params['date'],
            "group": query_params['group'],
            "teacher": query_params.get('teacher', '')
        }
        
        return await self._make_request(payload)

    async def fetch_batch_schedules(self, date_list: list[str], group_list: list[str]) -> dict:
        """Получение расписания для нескольких дат и групп"""
        results = {}
        
        async with self.semaphore:
            tasks = []
            for date in date_list:
                for group in group_list:
                    tasks.append(
                        self._make_request({
                            "date": date,
                            "group": group,
                            "teacher": ""
                        })
                    )
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            idx = 0
            for date in date_list:
                for group in group_list:
                    result = batch_results[idx]
                    if not isinstance(result, Exception) and result:
                        key = f"{date}_{group}"
                        results[key] = result
                    idx += 1
        
        return results

    async def _make_request(self, payload: dict) -> list | None:
        """Базовый метод для выполнения запроса к API"""
        try:
            if self.last_request_time:
                elapsed = datetime.now() - self.last_request_time
                if elapsed < self.request_interval:
                    await asyncio.sleep((self.request_interval - elapsed).total_seconds())

            async with self.session.post(
                Config.API_URL,
                headers={
                    "x-access-token": Config.API_TOKEN,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10
            ) as response:
                
                self.last_request_time = datetime.now()
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return None
                
                data = await response.json()
                
                if not isinstance(data, list):
                    logger.error(f"Invalid API response format: {data}")
                    return None
                
                logger.info(f"API request successful. Fetched {len(data)} records")
                return data

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return None

async def fetch_schedule_from_api(query_params: dict) -> list | None:
    """Основной интерфейс для получения расписания"""
    async with APIClient() as client:
        return await client.fetch_schedule(query_params)