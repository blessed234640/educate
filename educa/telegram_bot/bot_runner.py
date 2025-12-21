#!/usr/bin/env python3
"""
Telegram Bot для Educa - полная версия
"""
import asyncio
import logging
import os
import sys
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command

# Импортируем наши модули
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot.config import config
from telegram_bot.api_client import EducaAPIClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация
TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация API клиента
api_client = EducaAPIClient(config.API_BASE_URL)

# Состояния FSM
class AuthState(StatesGroup):
    waiting_username = State()
    waiting_password = State()

class CourseState(StatesGroup):
    browsing_courses = State()
    viewing_course = State()
    viewing_module = State()

# Хранилище сессий
user_sessions = {}
user_states = {}  # Для хранения временных данных

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_main_keyboard(is_auth: bool = False):
    """Главная клавиатура"""
    if is_auth:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Все курсы"), KeyboardButton(text="🎓 Мои курсы")],
                [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="📊 Прогресс")],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="❓ Помощь")],
                [KeyboardButton(text="🚪 Выход")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔐 Войти")],
                [KeyboardButton(text="📚 Курсы (гость)"), KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True
        )

def create_courses_keyboard(courses: list, page: int, total_pages: int, 
                           prefix: str = "course") -> InlineKeyboardMarkup:
    """Создает клавиатуру для списка курсов"""
    keyboard = []
    
    for course in courses:
        title = course.get('title', 'Без названия')[:30]
        keyboard.append([
            InlineKeyboardButton(
                text=f"📘 {title}",
                callback_data=f"{prefix}_{course['id']}"
            )
        ])
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current")
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page+1}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_course_detail_keyboard(course_id: int, is_enrolled: bool = False, 
                                 is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для деталей курса"""
    keyboard = []
    
    if not is_enrolled:
        keyboard.append([
            InlineKeyboardButton(
                text="🎓 Записаться на курс",
                callback_data=f"enroll_{course_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="📖 Открыть материалы",
                callback_data=f"contents_{course_id}"
            )
        ])
    
    # Кнопка избранного
    favorite_text = "❤️ В избранном" if is_favorite else "🤍 В избранное"
    keyboard.append([
        InlineKeyboardButton(
            text=favorite_text,
            callback_data=f"favorite_{course_id}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад к курсам", callback_data="back_to_courses"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

@dp.message(CommandStart())
async def start_cmd(message: Message):
    """Начало работы"""
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        username = user_sessions[user_id]["username"]
        await message.answer(
            f"🎓 *С возвращением, {username}!*\n\n"
            "Выберите раздел:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(is_auth=True)
        )
    else:
        await message.answer(
            "🎓 *Добро пожаловать в Educa Bot!*\n\n"
            "Я помогу вам:\n"
            "• Изучать курсы\n"
            "• Отслеживать прогресс\n"
            "• Учиться в удобном формате\n\n"
            "Для начала войдите в систему:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(is_auth=False)
        )

@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    """Помощь"""
    user_id = message.from_user.id
    is_auth = user_id in user_sessions
    
    help_text = "🤖 *Educa Bot - Помощь*\n\n"
    
    if is_auth:
        help_text += "*Для авторизованных:*\n"
        help_text += "📚 Все курсы - Все доступные курсы\n"
        help_text += "🎓 Мои курсы - Курсы, на которые вы записаны\n"
        help_text += "⭐ Избранное - Понравившиеся курсы\n"
        help_text += "📊 Прогресс - Ваш прогресс обучения\n"
        help_text += "👤 Профиль - Ваш профиль\n\n"
    else:
        help_text += "*Для гостей:*\n"
        help_text += "🔐 Войти - Авторизация\n"
        help_text += "📚 Курсы (гость) - Просмотр курсов\n\n"
    
    help_text += "*Общие команды:*\n"
    help_text += "/start - Начало работы\n"
    help_text += "/help - Эта справка\n"
    help_text += "/status - Статус бота\n"
    
    if is_auth:
        help_text += "/logout - Выйти из системы"
    
    await message.answer(help_text, parse_mode="Markdown")

# ========== АВТОРИЗАЦИЯ ==========

@dp.message(F.text == "🔐 Войти")
@dp.message(Command("login"))
async def login_cmd(message: Message, state: FSMContext):
    """Вход в систему"""
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        await message.answer("✅ Вы уже авторизованы!")
        return
    
    await state.set_state(AuthState.waiting_username)
    await message.answer("🔐 *Вход в систему*\n\nВведите ваш логин или email:")

@dp.message(AuthState.waiting_username)
async def process_username(message: Message, state: FSMContext):
    """Обработка логина"""
    username = message.text.strip()
    
    if not username:
        await message.answer("Пожалуйста, введите логин:")
        return
    
    await state.update_data(username=username)
    await state.set_state(AuthState.waiting_password)
    await message.answer(f"Логин: `{username}`\n\nТеперь введите пароль:")

@dp.message(AuthState.waiting_password)
async def process_password(message: Message, state: FSMContext):
    """Обработка пароля"""
    password = message.text.strip()
    user_data = await state.get_data()
    username = user_data['username']
    user_id = message.from_user.id
    
    await message.answer("🔐 Проверяю учетные данные...")
    
    result = await api_client.check_auth(username, password)
    
    if result.get("success"):
        user_sessions[user_id] = {
            "username": username,
            "auth": (username, password),
            "authenticated": True,
            "favorites": []  # Для хранения избранных курсов
        }
        
        await message.answer(
            f"✅ *Авторизация успешна!*\n\n"
            f"Добро пожаловать, {username}!\n\n"
            "Теперь вам доступны все функции:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(is_auth=True)
        )
    else:
        error = result.get("error", "Неизвестная ошибка")
        await message.answer(
            f"❌ *Ошибка авторизации*\n\n{error}\n\nПопробуйте снова: /login",
            parse_mode="Markdown"
        )
    
    await state.clear()

@dp.message(F.text == "🚪 Выход")
@dp.message(Command("logout"))
async def logout_cmd(message: Message):
    """Выход из системы"""
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        username = user_sessions[user_id]["username"]
        del user_sessions[user_id]
        await message.answer(
            f"👋 До свидания, {username}!\nВы вышли из системы.",
            reply_markup=get_main_keyboard(is_auth=False)
        )
    else:
        await message.answer("Вы не авторизованы.")

# ========== КУРСЫ ==========

@dp.message(F.text == "📚 Все курсы")
async def all_courses_cmd(message: Message):
    """Все курсы"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer(
            "Для просмотра курсов необходимо авторизоваться.\n\n"
            "Нажмите '🔐 Войти'",
            reply_markup=get_main_keyboard(is_auth=False)
        )
        return
    
    auth = user_sessions[user_id]["auth"]
    
    await message.answer("📚 Загружаю список курсов...")
    
    try:
        courses = await api_client.get_all_courses(auth, page=1)
        
        if not courses:
            await message.answer("📭 Курсы не найдены.")
            return
        
        # Сохраняем курсы во временное состояние
        user_states[user_id] = {
            "courses": courses,
            "current_page": 1,
            "total_pages": 5,  # Нужно получать из API
            "view_type": "all"
        }
        
        # Формируем сообщение
        response = "📚 *Все курсы:*\n\n"
        for i, course in enumerate(courses[:config.MAX_COURSES_PER_PAGE], 1):
            title = course.get('title', 'Без названия')
            overview = course.get('overview', '')[:50]
            response += f"{i}. *{title}*\n   {overview}...\n\n"
        
        # Создаем клавиатуру
        keyboard = create_courses_keyboard(
            courses[:config.MAX_COURSES_PER_PAGE],
            page=1,
            total_pages=5,
            prefix="course"
        )
        
        await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in all_courses_cmd: {e}")
        await message.answer("❌ Не удалось загрузить курсы.")

@dp.message(F.text == "🎓 Мои курсы")
async def my_courses_cmd(message: Message):
    """Мои курсы"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer("Сначала войдите: /login")
        return
    
    auth = user_sessions[user_id]["auth"]
    
    await message.answer("🎓 Загружаю ваши курсы...")
    
    try:
        # Получаем курсы пользователя
        courses = await api_client.get_enrolled_courses(auth)
        
        if not courses:
            await message.answer(
                "📭 Вы еще не записаны ни на один курс.\n\n"
                "Перейдите в 'Все курсы' чтобы записаться."
            )
            return
        
        # Сохраняем во временное состояние
        user_states[user_id] = {
            "courses": courses,
            "current_page": 1,
            "total_pages": 1,
            "view_type": "my"
        }
        
        response = "🎓 *Ваши курсы:*\n\n"
        for i, course in enumerate(courses, 1):
            title = course.get('title', 'Без названия')
            
            # Получаем прогресс
            progress = await api_client.get_course_progress(course['id'], auth)
            progress_percent = progress.get('progress_percentage', 0) if progress else 0
            
            response += f"{i}. *{title}*\n"
            response += f"   📊 Прогресс: {progress_percent}%\n\n"
        
        keyboard = create_courses_keyboard(
            courses,
            page=1,
            total_pages=1,
            prefix="mycourse"
        )
        
        await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in my_courses_cmd: {e}")
        await message.answer("❌ Не удалось загрузить ваши курсы.")

@dp.message(F.text == "⭐ Избранное")
async def favorites_cmd(message: Message):
    """Избранные курсы"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer("Сначала войдите: /login")
        return
    
    auth = user_sessions[user_id]["auth"]
    
    await message.answer("⭐ Загружаю избранные курсы...")
    
    try:
        favorites = user_sessions[user_id].get("favorites", [])
        
        if not favorites:
            await message.answer(
                "⭐ У вас пока нет избранных курсов.\n\n"
                "Добавляйте курсы в избранное из списка курсов."
            )
            return
        
        # Получаем детали избранных курсов
        courses = []
        for course_id in favorites:
            course = await api_client.get_course_detail(course_id, auth)
            if course:
                courses.append(course)
        
        response = "⭐ *Избранные курсы:*\n\n"
        for i, course in enumerate(courses, 1):
            title = course.get('title', 'Без названия')
            response += f"{i}. *{title}*\n\n"
        
        keyboard = create_courses_keyboard(
            courses,
            page=1,
            total_pages=1,
            prefix="favcourse"
        )
        
        await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in favorites_cmd: {e}")
        await message.answer("❌ Не удалось загрузить избранное.")

# ========== CALLBACK ОБРАБОТЧИКИ ==========

@dp.callback_query(F.data.startswith("course_"))
@dp.callback_query(F.data.startswith("mycourse_"))
@dp.callback_query(F.data.startswith("favcourse_"))
async def show_course_detail(callback: CallbackQuery):
    """Показать детали курса"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer("Сначала войдите в систему", show_alert=True)
        return
    
    # Извлекаем ID курса
    if callback.data.startswith("course_"):
        course_id = int(callback.data.split("_")[1])
        view_type = "all"
    elif callback.data.startswith("mycourse_"):
        course_id = int(callback.data.split("_")[1])
        view_type = "my"
    else:  # favcourse_
        course_id = int(callback.data.split("_")[1])
        view_type = "favorites"
    
    auth = user_sessions[user_id]["auth"]
    favorites = user_sessions[user_id].get("favorites", [])
    
    await callback.message.edit_text("📘 Загружаю информацию о курсе...")
    
    try:
        # Получаем детали курса
        course = await api_client.get_course_detail(course_id, auth)
        
        if not course:
            await callback.message.edit_text("❌ Курс не найден.")
            await callback.answer()
            return
        
        # Формируем описание
        title = course.get('title', 'Без названия')
        overview = course.get('overview', 'Нет описания')
        subject = course.get('subject', {}).get('title', 'Не указано')
        created = course.get('created', '')[:10]
        modules_count = len(course.get('modules', []))
        
        # Проверяем, записан ли пользователь
        is_enrolled = False
        if 'students' in course:
            # Нужна адаптация под вашу модель данных
            pass
        
        # Проверяем, в избранном ли
        is_favorite = course_id in favorites
        
        response = f"📘 *{title}*\n\n"
        response += f"📝 *Описание:*\n{overview}\n\n"
        response += f"📚 *Предмет:* {subject}\n"
        response += f"📅 *Создан:* {created}\n"
        response += f"📦 *Модулей:* {modules_count}\n\n"
        
        if is_enrolled:
            response += "✅ *Вы записаны на этот курс*\n\n"
        else:
            response += "📝 *Вы можете записаться на курс*\n\n"
        
        if is_favorite:
            response += "❤️ *В избранном*"
        
        # Создаем клавиатуру
        keyboard = create_course_detail_keyboard(
            course_id, 
            is_enrolled=is_enrolled,
            is_favorite=is_favorite
        )
        
        await callback.message.edit_text(
            response, 
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing course detail: {e}")
        await callback.message.edit_text("❌ Не удалось загрузить информацию о курсе.")
        await callback.answer()

@dp.callback_query(F.data.startswith("enroll_"))
async def enroll_to_course(callback: CallbackQuery):
    """Записаться на курс"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer("Сначала войдите в систему", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[1])
    auth = user_sessions[user_id]["auth"]
    
    await callback.message.edit_text("🎓 Записываю на курс...")
    
    try:
        success = await api_client.enroll_to_course(course_id, auth)
        
        if success:
            await callback.message.edit_text(
                "✅ *Вы успешно записались на курс!*\n\n"
                "Теперь вы можете изучать материалы курса.",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                "❌ *Не удалось записаться на курс*\n\n"
                "Возможно, вы уже записаны или произошла ошибка.",
                parse_mode="Markdown"
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error enrolling to course: {e}")
        await callback.message.edit_text("❌ Ошибка при записи на курс.")
        await callback.answer()

@dp.callback_query(F.data.startswith("contents_"))
async def show_course_contents(callback: CallbackQuery):
    """Показать содержимое курса"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer("Сначала войдите в систему", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[1])
    auth = user_sessions[user_id]["auth"]
    
    await callback.message.edit_text("📖 Загружаю материалы курса...")
    
    try:
        contents = await api_client.get_course_contents(course_id, auth)
        
        if not contents:
            await callback.message.edit_text("📭 Материалы курса не найдены.")
            await callback.answer()
            return
        
        response = "📖 *Материалы курса:*\n\n"
        
        for module in contents:
            module_title = module.get('title', 'Без названия')
            module_order = module.get('order', 0)
            contents_list = module.get('contents', [])
            
            response += f"📦 *Модуль {module_order}: {module_title}*\n"
            
            for content in contents_list:
                content_order = content.get('order', 0)
                item = content.get('item', {})
                item_type = item.get('type', 'material')
                item_title = item.get('title', 'Материал')
                
                icon = "📄" if item_type == "text" else "🎥" if item_type == "video" else "📎"
                response += f"   {icon} {content_order}. {item_title}\n"
            
            response += "\n"
        
        # Кнопка назад
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ К курсу", callback_data=f"course_{course_id}"),
                    InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
                ]
            ]
        )
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing contents: {e}")
        await callback.message.edit_text("❌ Не удалось загрузить материалы.")
        await callback.answer()

@dp.callback_query(F.data.startswith("favorite_"))
async def toggle_favorite(callback: CallbackQuery):
    """Добавить/удалить из избранного"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer("Сначала войдите в систему", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[1])
    
    # Простая реализация избранного (без API)
    if 'favorites' not in user_sessions[user_id]:
        user_sessions[user_id]['favorites'] = []
    
    favorites = user_sessions[user_id]['favorites']
    
    if course_id in favorites:
        favorites.remove(course_id)
        await callback.answer("💔 Удалено из избранного", show_alert=True)
    else:
        favorites.append(course_id)
        await callback.answer("❤️ Добавлено в избранное", show_alert=True)
    
    # Обновляем сообщение
    await show_course_detail(callback)

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    is_auth = user_id in user_sessions
    
    await callback.message.edit_text(
        "🏠 *Главное меню*\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(is_auth=is_auth)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: CallbackQuery):
    """Вернуться к списку курсов"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    # Можно сохранять тип просмотра (все/мои/избранное)
    # и возвращаться к соответствующему списку
    await all_courses_cmd(callback.message)
    await callback.answer()

# ========== ЗАПУСК БОТА ==========

async def main():
    """Основная функция запуска"""
    logger.info("=" * 50)
    logger.info("🤖 Educa Telegram Bot запускается...")
    logger.info(f"🌐 API URL: {config.API_BASE_URL}")
    logger.info("=" * 50)
    
    try:
        me = await bot.get_me()
        logger.info(f"✅ Бот: @{me.username} ({me.first_name})")
        logger.info("✅ Готов к работе!")
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    asyncio.run(main())

# ========== ПРОФИЛЬ ==========

@dp.message(F.text == "👤 Профиль")
async def profile_cmd(message: Message):
    """Профиль пользователя"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer(
            "Для просмотра профиля необходимо авторизоваться.\n\n"
            "Нажмите '🔐 Войти'",
            reply_markup=get_main_keyboard(is_auth=False)
        )
        return
    
    auth = user_sessions[user_id]["auth"]
    
    await message.answer("👤 Загружаю ваш профиль...")
    
    try:
        profile = await api_client.get_user_profile(auth)
        
        if not profile:
            await message.answer("❌ Не удалось загрузить профиль.")
            return
        
        user_info = profile.get('user', {})
        stats = profile.get('statistics', {})
        enrolled_courses = profile.get('enrolled_courses', [])
        
        response = "👤 *Ваш профиль*\n\n"
        response += f"👤 *Имя:* {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n"
        response += f"📧 *Email:* {user_info.get('email', 'Не указан')}\n"
        response += f"🔑 *Логин:* {user_info.get('username', '')}\n\n"
        
        response += "📊 *Статистика:*\n"
        response += f"• 📚 Курсов записано: {stats.get('enrolled_courses', 0)}\n"
        response += f"• ✅ Курсов завершено: {stats.get('completed_courses', 0)}\n"
        response += f"• 📈 Средний прогресс: {stats.get('average_progress', 0)}%\n\n"
        
        if enrolled_courses:
            response += "🎓 *Ваши курсы:*\n"
            for course in enrolled_courses[:5]:  # Показываем первые 5
                response += f"• {course.get('title', '')} - {course.get('progress', 0)}%\n"
            
            if len(enrolled_courses) > 5:
                response += f"\n... и еще {len(enrolled_courses) - 5} курсов"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in profile_cmd: {e}")
        await message.answer("❌ Не удалось загрузить профиль.")

# ========== ПРОГРЕСС ==========

@dp.message(F.text == "📊 Прогресс")
async def progress_cmd(message: Message):
    """Прогресс пользователя"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.answer(
            "Для просмотра прогресса необходимо авторизоваться.\n\n"
            "Нажмите '🔐 Войти'",
            reply_markup=get_main_keyboard(is_auth=False)
        )
        return
    
    auth = user_sessions[user_id]["auth"]
    
    await message.answer("📊 Загружаю ваш прогресс...")
    
    try:
        progress_data = await api_client.get_all_progress(auth)
        
        if not progress_data or 'courses' not in progress_data:
            await message.answer(
                "📭 У вас пока нет прогресса по курсам.\n\n"
                "Начните изучать курсы чтобы отслеживать прогресс."
            )
            return
        
        courses_progress = progress_data['courses']
        
        response = "📊 *Ваш прогресс по курсам:*\n\n"
        
        for i, course in enumerate(courses_progress[:5], 1):
            title = course.get('course_title', 'Без названия')
            progress = course.get('progress_percentage', 0)
            total_modules = course.get('total_modules', 0)
            completed_modules = course.get('completed_modules_count', 0)
            
            # Создаем прогресс-бар
            progress_bar = "🟩" * int(progress / 20) + "⬜" * (5 - int(progress / 20))
            
            response += f"{i}. *{title}*\n"
            response += f"   {progress_bar} {progress}%\n"
            response += f"   📦 Модулей: {completed_modules}/{total_modules}\n\n"
        
        if len(courses_progress) > 5:
            response += f"📄 И еще {len(courses_progress) - 5} курсов..."
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in progress_cmd: {e}")
        await message.answer("❌ Не удалось загрузить прогресс.")

# ========== КУРСЫ ДЛЯ ГОСТЕЙ ==========

@dp.message(F.text == "📚 Курсы (гость)")
async def guest_courses_cmd(message: Message):
    """Курсы для гостей"""
    await message.answer("📚 Загружаю курсы для гостевого просмотра...")
    
    try:
        courses = await api_client.get_guest_courses()
        
        if not courses:
            await message.answer("📭 Пока нет доступных курсов.")
            return
        
        response = "📚 *Доступные курсы (гостевой режим):*\n\n"
        response += "*Войдите в систему чтобы:*\n"
        response += "• Записаться на курсы\n"
        response += "• Отслеживать прогресс\n"
        response += "• Сохранять избранное\n\n"
        
        response += "*Примеры курсов:*\n"
        for i, course in enumerate(courses[:3], 1):
            title = course.get('title', 'Без названия')
            overview = course.get('overview', '')[:60]
            response += f"{i}. *{title}*\n   {overview}...\n\n"
        
        response += "🔐 *Для полного доступа:* /login"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in guest_courses_cmd: {e}")
        await message.answer("❌ Не удалось загрузить курсы для гостей.")