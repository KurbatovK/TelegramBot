import aiohttp
import json
from config import Config

async def fetch_schedule_from_api(query_params: dict):
    headers = {
        "x-access-token": Config.API_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "date": query_params['date'],
        "group": query_params['group'],
        "teacher": query_params['teacher']
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(Config.API_URL, headers=headers, data=json.dumps(payload)) as response:
            if response.status == 200:
                return await response.json()
            return []