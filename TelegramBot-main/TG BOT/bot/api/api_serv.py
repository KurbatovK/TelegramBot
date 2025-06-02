import aiohttp
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

async def fetch_schedule_from_api(query_params: dict):
    """Получает расписание с API с обработкой ошибок"""
    url = Config.API_URL
    headers = {
        "x-access-token": Config.API_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "date": query_params.get('date'),
        "group": query_params.get('group'),
        "teacher": query_params.get('teacher', '')
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return None
                
                data = await response.json()
                
                if not isinstance(data, list):
                    logger.error(f"Invalid API response format: {data}")
                    return None
                
                logger.info(f"Successfully fetched {len(data)} records from API")
                return data

    except aiohttp.ClientError as e:
        logger.error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode API response: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None