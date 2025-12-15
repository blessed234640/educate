from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards import (
    get_main_menu, get_courses_keyboard, 
    get_course_actions, get_contents_keyboard
)
from api.client import api

router = Router()

@router.message(F.text == "🏠 Главное меню")
@router.callback_query(F.data == "main_menu")
async def main_menu(event: Message | CallbackQuery, state: FSMContext):
    """Главное меню"""
    message = event if isinstance(event, Message) else event.message
    
    await state.clear()
    await message.answer(
        "📚 *Главное меню*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.message(F.text == "📚 Мои курсы")
async def my_courses(message: Message, state: FSMContext):
    """Показать курсы пользователя"""
    await state.update_data(course_type="my")
    
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await message.answer(
            "Сначала необходимо авторизоваться",
            reply_markup=get_auth_keyboard()
        )
        return
    
    # Получаем курсы с API
    courses = await api.get_user_courses(auth)
    
    if not courses:
        await message.answer(
            "📭 У вас пока нет записанных курсов\n\n"
            "Перейдите в 'Все курсы' чтобы выбрать интересующие вас курсы.",
            reply_markup=get_main_menu()
        )
        return
    
    # Сохраняем курсы в состоянии
    await state.update_data(my_courses=courses, current_page=1)
    
    # Формируем сообщение
    text = "📚 *Ваши курсы:*\n\n"
    for i, course in enumerate(courses[:5], 1):
        text += f"{i}. *{course.get('title', 'Без названия')}*\n"
        text += f"   📝 {course.get('overview', '')[:50]}...\n\n"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_courses_keyboard(courses, 1, is_my_courses=True)
    )

@router.message(F.text == "🎓 Все курсы")
async def all_courses(message: Message, state: FSMContext):
    """Все доступные курсы"""
    await state.update_data(course_type="all")
    
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await message.answer(
            "Сначала необходимо авторизоваться",
            reply_markup=get_auth_keyboard()
        )
        return
    
    courses_data = await api.get_all_courses(auth, page=1)
    courses = courses_data.get("results", []) if courses_data else []
    
    if not courses:
        await message.answer("📭 Курсы не найдены")
        return
    
    await state.update_data(all_courses=courses, current_page=1)
    
    text = "🎓 *Все курсы:*\n\n"
    for i, course in enumerate(courses[:5], 1):
        text += f"{i}. *{course.get('title', 'Без названия')}*\n"
        text += f"   👨‍🏫 {course.get('owner_name', 'Автор')}\n"
        text += f"   📝 {course.get('overview', '')[:50]}...\n\n"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_courses_keyboard(courses, 1, is_my_courses=False)
    )

@router.callback_query(F.data.startswith("course_"))
async def show_course(callback: CallbackQuery, state: FSMContext):
    """Показать детали курса"""
    course_id = int(callback.data.split("_")[1])
    
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await callback.message.answer(
            "Сначала необходимо авторизоваться",
            reply_markup=get_auth_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем детали курса
    course = await api.make_request(f"courses/{course_id}/", auth=auth)
    
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return
    
    # Проверяем, записан ли пользователь
    # (нужно будет доработать API для этого поля)
    is_enrolled = False  # Временно
    
    # Формируем текст
    text = f"""
📘 *{course.get('title', 'Без названия')}*

📝 *Описание:*
{course.get('overview', 'Нет описания')}

👨‍🏫 *Автор:* {course.get('owner_name', 'Неизвестен')}
📅 *Создан:* {course.get('created', '')[:10]}

"""
    
    if is_enrolled:
        text += "✅ Вы записаны на этот курс\n"
    else:
        text += "📝 Вы можете записаться на курс\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_course_actions(course_id, is_enrolled)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("enroll_"))
async def enroll_to_course(callback: CallbackQuery, state: FSMContext):
    """Записаться на курс"""
    course_id = int(callback.data.split("_")[1])
    
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await callback.answer("Сначала авторизуйтесь", show_alert=True)
        return
    
    result = await api.enroll_to_course(course_id, auth)
    
    if result:
        await callback.answer("✅ Вы успешно записались на курс!", show_alert=True)
        # Обновляем сообщение
        await show_course(callback, state)
    else:
        await callback.answer("❌ Не удалось записаться", show_alert=True)

@router.callback_query(F.data.startswith("contents_"))
async def show_course_contents(callback: CallbackQuery, state: FSMContext):
    """Показать содержимое курса"""
    course_id = int(callback.data.split("_")[1])
    
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await callback.answer("Сначала авторизуйтесь", show_alert=True)
        return
    
    contents = await api.get_course_contents(course_id, auth)
    
    if not contents:
        await callback.answer("Материалы не найдены", show_alert=True)
        return
    
    text = f"📖 *Материалы курса:*\n\n"
    
    for i, content in enumerate(contents, 1):
        item = content.get('item', {})
        text += f"{i}. {item.get('title', 'Материал')}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_contents_keyboard(contents, course_id)
    )
    await callback.answer()

@router.message(F.text == "📖 Продолжить обучение")
async def continue_learning(message: Message, state: FSMContext):
    """Продолжить обучение с последнего места"""
    user_data = await state.get_data()
    auth = user_data.get("auth")
    
    if not auth:
        await message.answer(
            "Сначала необходимо авторизоваться",
            reply_markup=get_auth_keyboard()
        )
        return
    
    # Получаем последний активный курс
    courses = await api.get_user_courses(auth)
    
    if not courses:
        await message.answer(
            "У вас пока нет активных курсов. Запишитесь на курс из раздела 'Все курсы'",
            reply_markup=get_main_menu()
        )
        return
    
    # Берем первый курс для примера
    last_course = courses[0]
    
    await message.answer(
        f"📚 *Продолжаем обучение*\n\n"
        f"Ваш последний курс:\n"
        f"*{last_course.get('title', 'Без названия')}*\n\n"
        f"Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_course_actions(last_course['id'], True)
    )