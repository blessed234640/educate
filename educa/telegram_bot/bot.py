import os
import sys
import logging
import asyncio
from pathlib import Path

# Добавляем родительскую директорию в путь Python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Теперь импортируем Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educate.settings')

import django
django.setup()

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# Локальные импорты (теперь они будут работать)
from .api_client import SecureAPIClient
from .handlers import BotHandlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class LearningBot:
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url
        
        # Инициализация клиента API
        self.api_client = SecureAPIClient()
        
        # Инициализация обработчиков
        self.handlers = BotHandlers(self.api_client)
        
        # Создание приложения
        self.application = Application.builder().token(token).build()
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help))
        self.application.add_handler(CommandHandler("status", self.handlers.status))
        
        # Callback запросы
        self.application.add_handler(
            CallbackQueryHandler(self.handlers.handle_callback_query)
        )
        
        # Текстовые сообщения
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message)
        )
        
        # Обработка ошибок
        self.application.add_error_handler(self._error_handler)
    
    async def _error_handler(self, update, context):
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        # Отправляем сообщение об ошибке пользователю
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте позже или свяжитесь с администратором."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
    
    def run(self):
        """Запуск бота"""
        logger.info("Starting Telegram bot...")
        
        # Запуск polling
        self.application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True,
            close_loop=False
        )


def run_bot():
    """Функция для запуска бота"""
    from django.conf import settings
    
    # Получение настроек
    TELEGRAM_BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    API_BASE_URL = getattr(settings, 'BASE_API_URL', 'http://localhost:8000/api')
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в настройках Django")
        print("Ошибка: TELEGRAM_BOT_TOKEN не найден в settings.py")
        print("Добавьте в settings.py:")
        print("TELEGRAM_BOT_TOKEN = 'ваш_токен'")
        sys.exit(1)
    
    # Проверяем API ключи
    TELEGRAM_BOT_API_KEY = getattr(settings, 'TELEGRAM_BOT_API_KEY', None)
    TELEGRAM_BOT_API_SECRET = getattr(settings, 'TELEGRAM_BOT_API_SECRET', None)
    
    if not TELEGRAM_BOT_API_KEY or not TELEGRAM_BOT_API_SECRET:
        logger.warning("API ключи для бота не установлены. Используйте .env файл")
    
    # Создание и запуск бота
    bot = LearningBot(TELEGRAM_BOT_TOKEN, API_BASE_URL)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    # Для запуска напрямую
    run_bot()