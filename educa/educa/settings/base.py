from pathlib import Path
import os
from django.urls import reverse_lazy
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

LOGIN_REDIRECT_URL = reverse_lazy("student_course_list")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "uxeUXnTbz6E7LuGWlWB491Ldhf29SebVAIUA3aldGeqfK3LR8sgdIi21A8coNpp6wag")

ALLOWED_HOSTS = []

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY", "telegram_bot_key")
TELEGRAM_BOT_API_SECRET = os.getenv("TELEGRAM_BOT_API_SECRET", "telegram_bot_secret")

# API Settings
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

INSTALLED_APPS = [
    "daphne",
    "courses.apps.CoursesConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "students.apps.StudentsConfig",
    "braces",
    "tinymce",
    "embed_video",
    "debug_toolbar",
    "redisboard",
    "rest_framework",
    "chat.apps.ChatConfig",
    "telegram_bot",  # Добавляем приложение бота
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'students.middleware.TrackStudentProgressMiddleware',
]

ROOT_URLCONF = "educa.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "educa.wsgi.application"
ASGI_APPLICATION = "educa.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379"),
    }
}

INTERNAL_IPS = ["127.0.0.1"]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}

TINYMCE_DEFAULT_CONFIG = {
    "height": "300px",
    "width": "100%",
    "menubar": False,
    "plugins": "link image lists code",
    "toolbar": "undo redo | bold italic | alignleft aligncenter alignright | link image | bullist numlist | code",
    "branding": False,
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379")],
        },
    },
}