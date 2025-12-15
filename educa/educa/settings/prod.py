from decouple import config

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
]
