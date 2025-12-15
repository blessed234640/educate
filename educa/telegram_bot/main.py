# main.py - исправленная версия
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# Инициализация
bot = Bot(token="8553270096:AAF6P9wlhzrtx-zcrOO77J5uUS7BoTS_d3g")
dp = Dispatcher(storage=MemoryStorage())

# Временное хранилище для авторизации
user_auth = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎓 *Добро пожаловать в обучающую платформу Educa!*\n\n"
        "Я помогу вам учиться прямо в Telegram.\n\n"
        "Для начала работы необходимо авторизоваться.\n\n"
        "Используйте /auth для входа или /help для помощи.",
        parse_mode="Markdown"
    )

@dp.message(Command("auth"))
async def cmd_auth(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Telegram не принимает localhost в URL кнопок
    # Временное решение: показываем ссылку как текст
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Проверить авторизацию", 
                callback_data="check_auth"
            )],
            [InlineKeyboardButton(
                text="🔐 Тестовый вход", 
                callback_data="test_login"
            )]
        ]
    )
    
    await message.answer(
        "🔐 *Авторизация*\n\n"
        "1. Откройте в браузере:\n"
        "   http://localhost:8000/accounts/login/\n\n"
        "2. Авторизуйтесь на сайте\n"
        "3. Вернитесь и нажмите 'Проверить авторизацию'\n\n"
        "Или используйте 'Тестовый вход' для быстрого тестирования.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "check_auth")
async def check_auth(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_auth.get(user_id):
        await callback.message.answer(
            "✅ Вы авторизованы!\n\n"
            "Теперь вам доступны все функции бота.\n\n"
            "Используйте /menu для главного меню."
        )
    else:
        await callback.message.answer(
            "❌ Вы не авторизованы\n\n"
            "Чтобы авторизоваться:\n"
            "1. Откройте http://localhost:8000/accounts/login/\n"
            "2. Войдите в свой аккаунт\n"
            "3. Вернитесь и проверьте снова\n\n"
            "Или используйте 'Тестовый вход' для быстрого тестирования."
        )
    
    await callback.answer()

@dp.callback_query(F.data == "test_login")
async def test_login(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_auth[user_id] = {
        "username": f"user_{user_id}",
        "user_id": user_id,
        "authenticated": True
    }
    
    await callback.message.answer(
        "✅ *Тестовый вход выполнен!*\n\n"
        "Теперь вы можете:\n"
        "• /menu - Главное меню\n"
        "• /courses - Все курсы\n"
        "• /my_courses - Мои курсы\n"
        "• /profile - Профиль\n\n"
        "В реальной версии будет интеграция с сайтом."
    )
    await callback.answer()

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    user_id = message.from_user.id
    
    if not user_auth.get(user_id):
        await message.answer(
            "Сначала нужно авторизоваться. Используйте /auth"
        )
        return
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Мои курсы"), KeyboardButton(text="🎓 Все курсы")],
            [KeyboardButton(text="📖 Продолжить"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📚 *Главное меню*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.message(Command("courses"))
@dp.message(F.text == "🎓 Все курсы")
async def all_courses(message: Message):
    user_id = message.from_user.id
    
    if not user_auth.get(user_id):
        await message.answer("Сначала авторизуйтесь: /auth")
        return
    
    # Простая разметка без звездочек внутри текста
    response = (
        "🎓 *Доступные курсы:*\n\n"
        "1. *Python для начинающих*\n"
        "   Рейтинг: 4.8/5\n"
        "   Длительность: 12 часов\n"
        "   Модулей: 8\n\n"
        "2. *Django с нуля*\n"
        "   Рейтинг: 4.9/5\n"
        "   Длительность: 20 часов\n"
        "   Модулей: 10\n\n"
        "3. *Базы данных SQL*\n"
        "   Рейтинг: 4.7/5\n"
        "   Длительность: 15 часов\n"
        "   Модулей: 7\n\n"
        "Скоро будет интеграция с реальными курсами!"
    )
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(Command("my_courses"))
@dp.message(F.text == "📚 Мои курсы")
async def my_courses(message: Message):
    user_id = message.from_user.id
    
    if not user_auth.get(user_id):
        await message.answer("Сначала авторизуйтесь: /auth")
        return
    
    response = (
        "📚 *Ваши курсы:*\n\n"
        "1. *Python для начинающих*\n"
        "   Прогресс: 60% завершено\n"
        "   Последний урок: Вчера\n\n"
        "2. *Django с нуля*\n"
        "   Прогресс: 30% завершено\n"
        "   Последний урок: 2 дня назад\n\n"
        "Скоро будет интеграция с реальными данными!"
    )
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text == "📖 Продолжить")
async def continue_learning(message: Message):
    user_id = message.from_user.id
    
    if not user_auth.get(user_id):
        await message.answer("Сначала авторизуйтесь: /auth")
        return
    
    response = (
        "📖 *Продолжаем обучение:*\n\n"
        "*Python для начинающих*\n"
        "Модуль 4: Работа с функциями\n\n"
        "Завершено: 3 из 5 заданий\n"
        "Время урока: 25 минут\n\n"
        "Скоро можно будет продолжить прямо здесь!"
    )
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = message.from_user.id
    
    if not user_auth.get(user_id):
        await message.answer("Сначала авторизуйтесь: /auth")
        return
    
    response = (
        "👤 *Ваш профиль:*\n\n"
        "Имя: Тестовый пользователь\n"
        "Курсов: 2\n"
        "Завершено: 1\n"
        "В процессе: 1\n"
        "Общий прогресс: 45%\n\n"
        "Скоро будет реальный профиль!"
    )
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await cmd_menu(message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    # Простая разметка без звездочек
    help_text = (
        "📚 *Помощь по боту Educa:*\n\n"
        "*Авторизация:*\n"
        "/start - Начало работы\n"
        "/auth - Авторизация\n"
        "/menu - Главное меню\n\n"
        "*Обучение:*\n"
        "/courses - Все курсы\n"
        "/my_courses - Мои курсы\n"
        "Продолжить - Продолжить обучение\n"
        "Профиль - Ваш профиль\n\n"
        "*Навигация:*\n"
        "Главное меню - Вернуться в меню"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("test"))
async def cmd_test(message: Message):
    await message.answer("✅ Бот работает!")

@dp.message(Command("status"))
async def cmd_status(message: Message):
    user_id = message.from_user.id
    is_auth = user_auth.get(user_id, False)
    
    status = "✅ Авторизован" if is_auth else "❌ Не авторизован"
    await message.answer(f"Статус: {status}\nID: {user_id}")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    print("=" * 50)
    print("🤖 Бот запускается...")
    print("Токен: 8553270096:AAF6P9wlhzrtx-zcrOO77J5uUS7BoTS_d3g")
    print("=" * 50)
    
    try:
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username} ({me.first_name})")
        print("📝 Команды для теста:")
        print("  /start - Приветствие")
        print("  /auth - Авторизация")
        print("  /menu - Главное меню")
        print("  /status - Проверить статус")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())