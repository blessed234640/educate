import aiohttp
import base64
import logging
from typing import Optional, Tuple, Dict, Any, List
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)

class EducaAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def _create_auth_headers(self, auth: Optional[Tuple[str, str]] = None) -> Dict:
        """Создает заголовки с Basic Auth"""
        headers = {
            'User-Agent': 'TelegramBot/1.0',
            'Accept': 'application/json',
        }
        
        if auth and len(auth) == 2:
            username, password = auth
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
            
        return headers
    
    async def _make_request(self, endpoint: str, method: str = "GET", 
                           auth: Optional[Tuple[str, str]] = None, **kwargs) -> Any:
        """Универсальный метод для запросов"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._create_auth_headers(auth)
        
        # Обновляем заголовки из kwargs
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                ) as response:
                    
                    logger.info(f"API Request: {method} {url} -> {response.status}")
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 201:
                        return await response.json()
                    else:
                        try:
                            error_data = await response.json()
                            return {"error": error_data, "status_code": response.status}
                        except:
                            error_text = await response.text()
                            return {"error": f"HTTP {response.status}: {error_text[:200]}", 
                                   "status_code": response.status}
                            
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"error": str(e), "status_code": 0}
    
    # ========== Аутентификация ==========
    
    async def check_auth(self, username: str, password: str) -> Dict:
        """Проверка аутентификации"""
        try:
            result = await self._make_request("courses/", auth=(username, password))
            
            if isinstance(result, dict) and "error" in result:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "status_code": result.get("status_code", 401)
                }
            
            return {
                "success": True,
                "username": username,
                "auth": (username, password)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== Курсы ==========
    
    async def get_all_courses(self, auth: Tuple[str, str], page: int = 1) -> List[Dict]:
        """Все курсы"""
        result = await self._make_request(f"courses/?page={page}", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting courses: {result.get('error')}")
            return []
            
        return result.get("results", [])
    
    async def get_course_detail(self, course_id: int, auth: Tuple[str, str]) -> Optional[Dict]:
        """Детали курса"""
        result = await self._make_request(f"courses/{course_id}/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting course {course_id}: {result.get('error')}")
            return None
            
        return result
    
    async def get_course_contents(self, course_id: int, auth: Tuple[str, str]) -> List[Dict]:
        """Содержимое курса"""
        result = await self._make_request(f"courses/{course_id}/contents/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting contents for course {course_id}: {result.get('error')}")
            return []
            
        return result.get("modules", []) if isinstance(result, dict) else result
    
    async def enroll_to_course(self, course_id: int, auth: Tuple[str, str]) -> bool:
        """Записаться на курс"""
        result = await self._make_request(
            f"courses/{course_id}/enroll/",
            method="POST",
            auth=auth
        )
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error enrolling to course {course_id}: {result.get('error')}")
            return False
            
        return True
    
    async def get_enrolled_courses(self, auth: Tuple[str, str]) -> List[Dict]:
        """Курсы, на которые записан пользователь"""
        result = await self._make_request("courses/my-courses/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting enrolled courses: {result.get('error')}")
            return []
            
        return result.get("results", [])
    
    # ========== Прогресс ==========
    
    async def get_course_progress(self, course_id: int, auth: Tuple[str, str]) -> Dict:
        """Прогресс по курсу"""
        result = await self._make_request(f"courses/{course_id}/progress/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting progress for course {course_id}: {result.get('error')}")
            return {}
            
        return result
    
    async def get_all_progress(self, auth: Tuple[str, str]) -> Dict:
        """Весь прогресс пользователя"""
        result = await self._make_request("progress/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting all progress: {result.get('error')}")
            return {}
            
        return result
    
    async def update_progress(self, course_id: int, module_id: int, 
                             completed: bool, auth: Tuple[str, str]) -> bool:
        """Обновить прогресс"""
        data = {
            "module_id": module_id,
            "completed": completed
        }
        
        result = await self._make_request(
            f"courses/{course_id}/progress/",
            method="POST",
            auth=auth,
            json=data
        )
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error updating progress: {result.get('error')}")
            return False
            
        return True
    
    # ========== Профиль пользователя ==========
    
    async def get_user_profile(self, auth: Tuple[str, str]) -> Dict:
        """Получить профиль пользователя"""
        result = await self._make_request("user/profile/", auth=auth)
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting user profile: {result.get('error')}")
            return {}
            
        return result
    
    # ========== Гостевой режим ==========
    
    async def get_guest_courses(self) -> List[Dict]:
        """Курсы для гостей (без авторизации)"""
        result = await self._make_request("courses/")
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error getting guest courses: {result.get('error')}")
            return []
            
        return result.get("results", [])

# Синглтон
api_client = None

def get_api_client():
    global api_client
    if api_client is None:
        from .config import config
        api_client = EducaAPIClient(config.API_BASE_URL)
    return api_client