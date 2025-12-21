import aiohttp
import base64
from typing import Optional, Dict, Any, Tuple
from config import config
python
import sys
import os

# Добавляем путь для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ApiClient:
    def __init__(self):
        self.base_url = config.API_BASE_URL
        
    async def make_request(self, endpoint: str, method: str = "GET", 
                          auth: Optional[Tuple[str, str]] = None, **kwargs):
        """Универсальный метод для запросов"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Добавляем заголовки
        headers = kwargs.pop('headers', {})
        headers.update({
            'User-Agent': 'TelegramBot/1.0',
            'Accept': 'application/json',
        })
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                auth=auth,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                **kwargs
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    return {"error": "Authentication failed"}
                elif response.status == 404:
                    return {"error": "Not found"}
                else:
                    try:
                        error_data = await response.json()
                        return {"error": error_data}
                    except:
                        return {"error": f"HTTP {response.status}"}
    
    def create_api_auth(self) -> Tuple[str, str]:
        """Создает аутентификацию для API через Basic Auth"""
        api_key = config.API_KEY
        api_secret = config.API_SECRET
        return (api_key, api_secret)
    
    async def check_user_auth(self, username: str, password: str) -> Dict:
        """Проверка аутентификации пользователя через API"""
        try:
            # Используем Basic Auth с учетными данными пользователя
            result = await self.make_request(
                "courses/", 
                auth=(username, password),
                method="GET"
            )
            
            if result and "error" not in result:
                return {
                    "success": True,
                    "username": username,
                    "auth": (username, password)
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_user_courses(self, auth: Tuple[str, str], page: int = 1):
        """Получить курсы пользователя"""
        # Получаем все курсы
        result = await self.make_request(
            f"courses/?page={page}", 
            auth=auth
        )
        
        if not result or "error" in result:
            return []
        
        # Фильтруем курсы по записи (нужно дополнение в API)
        all_courses = result.get("results", [])
        
        # Временно возвращаем все курсы
        # В будущем нужно добавить в API endpoint для курсов пользователя
        return all_courses
    
    async def get_all_courses(self, auth: Tuple[str, str], page: int = 1):
        """Все курсы"""
        return await self.make_request(f"courses/?page={page}", auth=auth)
    
    async def enroll_to_course(self, course_id: int, auth: Tuple[str, str]):
        """Записаться на курс"""
        result = await self.make_request(
            f"courses/{course_id}/enroll/",
            method="POST",
            auth=auth
        )
        return result and "enrolled" in result
    
    async def get_course_contents(self, course_id: int, auth: Tuple[str, str]):
        """Содержимое курса"""
        return await self.make_request(f"courses/{course_id}/contents/", auth=auth)
    
    async def get_course_progress(self, course_id: int, auth: Tuple[str, str]):
        """Прогресс по курсу"""
        return await self.make_request(f"courses/{course_id}/progress/", auth=auth)
    
    async def update_progress(self, course_id: int, module_id: int, 
                            completed: bool, auth: Tuple[str, str]):
        """Обновить прогресс"""
        data = {
            "module_id": module_id,
            "completed": completed
        }
        return await self.make_request(
            f"courses/{course_id}/progress/",
            method="POST",
            auth=auth,
            json=data
        )

# Синглтон
api_client = ApiClient()