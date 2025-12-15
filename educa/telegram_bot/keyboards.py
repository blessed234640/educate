from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import config

def get_auth_keyboard():
    """Клавиатура для неавторизованных пользователей"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🌐 Войти на сайте",
            url=f"{config.SITE_URL}/accounts/login/"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Проверить авторизацию",
            callback_data="check_auth"
        )
    )
    return builder.as_markup()

def get_main_menu():
    """Главное меню для авторизованных"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📚 Мои курсы"),
        KeyboardButton(text="🎓 Все курсы")
    )
    builder.row(
        KeyboardButton(text="📖 Продолжить обучение"),
        KeyboardButton(text="👤 Профиль")
    )
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

def get_courses_keyboard(courses: list, page: int, is_my_courses: bool = False):
    """Клавиатура со списком курсов"""
    builder = InlineKeyboardBuilder()
    
    # Курсы (максимум 5 на странице)
    for course in courses[:5]:
        course_title = course.get('title', 'Без названия')[:30]
        builder.row(
            InlineKeyboardButton(
                text=f"📘 {course_title}",
                callback_data=f"course_{course['id']}"
            )
        )
    
    # Навигация
    nav_row = []
    if page > 1:
        prefix = "my_" if is_my_courses else "all_"
        nav_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}courses_{page-1}")
        )
    
    nav_row.append(
        InlineKeyboardButton(text=f"{page}", callback_data="current_page")
    )
    
    if len(courses) == 5:  # Есть следующая страница
        prefix = "my_" if is_my_courses else "all_"
        nav_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"{prefix}courses_{page+1}")
        )
    
    if nav_row:
        builder.row(*nav_row)
    
    # Кнопка назад
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_course_actions(course_id: int, is_enrolled: bool):
    """Действия с курсом"""
    builder = InlineKeyboardBuilder()
    
    if not is_enrolled:
        builder.row(
            InlineKeyboardButton(
                text="🎓 Записаться на курс",
                callback_data=f"enroll_{course_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📖 Открыть материалы",
                callback_data=f"contents_{course_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к курсам", callback_data="back_to_courses"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_contents_keyboard(contents: list, course_id: int):
    """Навигация по материалам курса"""
    builder = InlineKeyboardBuilder()
    
    for i, content in enumerate(contents, 1):
        content_type = content.get('item', {}).get('type', 'material')
        icon = "📄" if content_type == "text" else "🎥" if content_type == "video" else "📎"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} Материал {i}",
                callback_data=f"material_{course_id}_{i}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ К курсу", callback_data=f"course_{course_id}"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
    )
    
    return builder.as_markup()