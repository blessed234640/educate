import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.conf import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Инициализация бота
TELEGRAM_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
if not TELEGRAM_TOKEN:
    logger.error("❌ Токен бота не найден в настройках!")
    sys.exit(1)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния FSM
class AuthState(StatesGroup):
    waiting_username = State()
    waiting_password = State()

# Временное хранилище сессий
user_sessions = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Начало работы"""
    await message.answer(
        "🎓 *Educa Bot*\n\n"
        "Добро пожаловать в систему обучения!\n\n"
        "Доступные команды:\n"
        "/login - Вход в систему\n"
        "/courses - Все курсы\n"
        "/help - Помощь\n\n"
        "Бот работает в Docker контейнере ✅",
        parse_mode="Markdown"
    )

@dp.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext):
    """Команда входа"""
    await state.set_state(AuthState.waiting_username)
    await message.answer("Введите ваш логин (email) с сайта:")

@dp.message(AuthState.waiting_username)
async def process_username(message: Message, state: FSMContext):
    """Обработка логина"""
    await state.update_data(username=message.text.strip())
    await state.set_state(AuthState.waiting_password)
    await message.answer("Введите ваш пароль:")

@dp.message(AuthState.waiting_password)
async def process_password(message: Message, state: FSMContext):
    """Обработка пароля"""
    from django.contrib.auth import authenticate
    
    user_data = await state.get_data()
    username = user_data['username']
    password = message.text.strip()
    
    user_id = message.from_user.id
    
    await message.answer("🔐 Проверяю учетные данные...")
    
    try:
        # Аутентификация через Django
        user = authenticate(username=username, password=password)
        
        if user is not None:
            user_sessions[user_id] = {
                "username": username,
                "user_id": user.id,
                "authenticated": True
            }
            
            await message.answer(
                f"✅ Вход выполнен!\n\n"
                f"Добро пожаловать, {username}!\n\n"
                "Теперь используйте:\n"
                "/courses - для просмотра курсов\n"
                "/menu - для главного меню",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Неверный логин или пароль")
            
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {e}")
        await message.answer("❌ Ошибка при входе. Попробуйте позже.")
    
    await state.clear()

@dp.message(Command("courses"))
async def all_courses(message: Message):
    """Все курсы"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer("Сначала войдите: /login")
        return
    
    await message.answer(
        "📚 *Доступные курсы:*\n\n"
        "1. Python для начинающих\n"
        "2. Django Web Development\n"
        "3. Базы данных SQL\n"
        "4. Алгоритмы и структуры данных\n"
        "5. Машинное обучение\n\n"
        "В режиме разработки...",
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Главное меню"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Курсы"), KeyboardButton(text="📊 Прогресс")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📱 *Главное меню*\n\n"
        "Выберите раздел:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    help_text = """
🤖 *Educa Bot - Помощь*

*Основные команды:*
/start - Начало работы
/login - Войти в систему
/courses - Показать курсы
/menu - Главное меню

*Дополнительно:*
/help - Эта справка
/status - Статус бота

*Бот работает в Docker контейнере*
Версия: 1.0.0
"""
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Статус бота"""
    user_id = message.from_user.id
    is_auth = user_id in user_sessions
    
    status_text = f"""
🤖 *Статус Educa Bot*

👤 ID: {user_id}
🔐 Auth: {'✅' if is_auth else '❌'}
🐳 Docker: ✅
🌐 API: {getattr(settings, 'API_BASE_URL', 'Not set')}

Сессий: {len(user_sessions)}
"""
    await message.answer(status_text, parse_mode="Markdown")

@dp.message(F.text == "📚 Курсы")
async def courses_button(message: Message):
    await all_courses(message)

@dp.message()
async def handle_unknown(message: Message):
    """Неизвестные команды"""
    await message.answer(
        "Не понимаю команду. Используйте /help для списка команд."
    )

async def main():
    """Запуск бота"""
    logger.info("=" * 50)
    logger.info("🤖 Educa Telegram Bot запускается...")
    logger.info(f"Токен: {'установлен' if TELEGRAM_TOKEN else 'НЕ УСТАНОВЛЕН!'}")
    logger.info("=" * 50)
    
    try:
        # Проверка бота
        me = await bot.get_me()
        logger.info(f"✅ Бот: @{me.username} ({me.first_name})")
        
        # Запуск
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise