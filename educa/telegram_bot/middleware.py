from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from api.client import api_client

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем команды старт и помощь без проверки
        if isinstance(event, Message) and event.text in ["/start", "/help"]:
            return await handler(event, data)
        
        # Проверяем авторизацию через API
        user_data = data.get("user_data", {})
        
        if not user_data.get("auth"):
            # Пользователь не авторизован - показываем кнопку входа
            if isinstance(event, Message):
                await event.answer(
                    "🔒 Для использования бота необходимо авторизоваться на сайте",
                    reply_markup=get_auth_keyboard()
                )
            elif isinstance(event, CallbackQuery):
                await event.message.answer(
                    "🔒 Для использования бота необходимо авторизоваться на сайте",
                    reply_markup=get_auth_keyboard()
                )
            return
        
        return await handler(event, data)