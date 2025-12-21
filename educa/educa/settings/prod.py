from decouple import config
import os
from .base import *

DEBUG = False
ADMINS = [
    ("Artur A", "arturazimov200577@gmail.com"),
]

ALLOWED_HOSTS = [
    "educaproject.com",
    "www.educaproject.com",
    "192.168.3.6",
    "ethically-polished-brill.cloudpub.ru",
    "web",  # для внутренней сети Docker
    "telegram-bot",  # для доступа бота

]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": "db",
        "PORT": 5432,
    }
}
REDIS_URL = "redis://cache:6379"
CACHES["default"]["LOCATION"] = REDIS_URL
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = [REDIS_URL]

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_BOT_API_KEY = config("TELEGRAM_BOT_API_KEY", default="telegram_api_key_123")
TELEGRAM_BOT_API_SECRET = config("TELEGRAM_BOT_API_SECRET", default="telegram_api_secret_456")

# Внутренние URL для Docker сети
API_BASE_URL = config("API_BASE_URL", default="http://web:8000/api")
SITE_URL = config("SITE_URL", default="http://web:8000")

# Внешние URL для пользователей
EXTERNAL_API_URL = config("EXTERNAL_API_URL", default="https://ethically-polished-brill.cloudpub.ru/api")
EXTERNAL_SITE_URL = config("EXTERNAL_SITE_URL", default="https://ethically-polished-brill.cloudpub.ru")

# Безопасность
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# КРИТИЧЕСКИ ВАЖНЫЕ НАСТРОЙКИ ДЛЯ РАБОТЫ ЧЕРЕЗ CLOUDPUB
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

CSRF_TRUSTED_ORIGINS = [
    "https://educaproject.com",
    "https://www.educaproject.com",
    "https://192.168.3.6",
    "https://ethically-polished-brill.cloudpub.ru",  # Обратите внимание на https://
    "http://web:8000",  # для внутренних запросов
]
# Настройки для телеграм бота
TELEGRAM_BOT_WEBHOOK_URL = f"{EXTERNAL_SITE_URL}/telegram/webhook/"
TELEGRAM_BOT_ALLOWED_USERS = []