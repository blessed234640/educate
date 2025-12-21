from django.apps import AppConfig
import asyncio
import threading

class TelegramBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'
    verbose_name = 'Telegram Bot'
    
    def ready(self):
        # Запускаем бота только в production или по флагу
        if not self.is_running_bot():
            return
            
        try:
            from .bot_runner import run_bot_async
            # Запускаем бота в отдельном потоке
            bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            bot_thread.start()
            print("✅ Telegram Bot запущен в фоновом режиме")
        except Exception as e:
            print(f"❌ Ошибка запуска Telegram Bot: {e}")
    
    def run_bot(self):
        """Запуск бота в синхронном режиме"""
        import asyncio
        from .bot_runner import run_bot_async
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bot_async())
    
    def is_running_bot(self):
        """Проверяем, нужно ли запускать бота"""
        import sys
        # Не запускаем при миграциях и тестах
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return False
        if 'test' in sys.argv:
            return False
        if 'runserver' in sys.argv:
            return True
        # В продакшене всегда запускаем
        return True