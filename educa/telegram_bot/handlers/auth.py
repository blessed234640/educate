from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import get_auth_keyboard, get_main_menu
from api.client import api

router = Router()

@router.message(Command("auth"))
@router.callback_query(F.data == "check_auth")
async def check_authentication(event: Message | CallbackQuery, state: FSMContext):
    """Проверка авторизации пользователя"""
    
    # В реальном боте здесь будет запрос к API для проверки
    # Пока используем упрощенную логику
    
    message = event if isinstance(event, Message) else event.message
    
    await message.answer(
        "🔐 *Проверка авторизации*\n\n"
        "Для работы с ботом необходимо:\n"
        "1. Открыть сайт по кнопке ниже\n"
        "2. Войти в свой аккаунт\n"
        "3. Вернуться и нажать 'Проверить авторизацию'\n\n"
        "После этого вы получите доступ ко всем курсам.",
        parse_mode="Markdown",
        reply_markup=get_auth_keyboard()
    )