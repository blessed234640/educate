import aiohttp
import json
from typing import Optional, Dict, Any, Tuple
from config import config

class ApiClient:
    def __init__(self):
        self.base_url = config.API_BASE_URL
        
    async def make_request(self, endpoint: str, method: str = "GET", 
                          auth: Optional[Tuple[str, str]] = None, **kwargs):
        """Универсальный метод для запросов"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                auth=auth,
                **kwargs
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def check_auth(self, auth: Tuple[str, str]) -> bool:
        """Проверка валидности авторизации"""
        try:
            result = await self.make_request("courses/", auth=auth)
            return result is not None
        except:
            return False
    
    async def get_user_courses(self, auth: Tuple[str, str], page: int = 1):
        """Получить курсы пользователя"""
        all_courses = await self.make_request(f"courses/?page={page}", auth=auth)
        if not all_courses:
            return []
        
        # Фильтруем курсы, на которые записан пользователь
        # (В вашем API нужно проверять поле students)
        my_courses = []
        for course in all_courses.get("results", []):
            # Проверяем, записан ли пользователь на курс
            # Для этого нужен дополнительный запрос или измененный API
            course_detail = await self.make_request(f"courses/{course['id']}/", auth=auth)
            if course_detail and course_detail.get("is_enrolled", False):
                my_courses.append(course)
        
        return my_courses
    
    async def get_all_courses(self, auth: Tuple[str, str], page: int = 1):
        """Все курсы"""
        return await self.make_request(f"courses/?page={page}", auth=auth)
    
    async def enroll_to_course(self, course_id: int, auth: Tuple[str, str]):
        """Записаться на курс"""
        return await self.make_request(
            f"courses/{course_id}/enroll/",
            method="POST",
            auth=auth
        )
    
    async def get_course_contents(self, course_id: int, auth: Tuple[str, str]):
        """Содержимое курса"""
        return await self.make_request(f"courses/{course_id}/contents/", auth=auth)

# Синглтон
api = ApiClient()