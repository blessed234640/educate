# 🎓 E-Learning Platform with Telegram Bot

## 📚 О проекте
Современная образовательная платформа для онлайн-курсов с полнофункциональным API, системой кэширования, чатом в реальном времени и интеграцией с Telegram ботом. Проект построен на Django с использованием современных технологий для масштабируемости и производительности.

## 🚀 Основные возможности

### 📖 Учебный контент
- **Многоуровневая структура курсов** (курсы → модули → уроки)
- **Поддержка различных типов контента** (текст, видео, изображения, файлы)
- **Система отслеживания прогресса студентов**
- **Гибкая система оценивания**

### 🤖 Telegram Bot
- **Интеграция с платформой через REST API**
- **Уведомления о новых курсах и материалах**
- **Отслеживание прогресса обучения**
- **Интерактивное взаимодействие с пользователями**

### 💬 Система общения
- **Чат в реальном времени** с использованием WebSockets (Django Channels)
- **Групповые и приватные беседы**
- **История сообщений**

### 🔧 Технические возможности
- **RESTful API** (Django REST Framework)
- **Кэширование с Redis и Memcached**
- **Контейнеризация с Docker**
- **Поддержка PostgreSQL и Redis**
- **Микросервисная архитектура**

## 🏗️ Архитектура системы

```mermaid
graph TB
    %% Клиенты
    Web[Веб-интерфейс] --> API[Django API Gateway]
    Mobile[Мобильные приложения] --> API
    Telegram[Telegram Bot] --> API
    
    %% Основные сервисы
    API --> Auth[Сервис аутентификации]
    API --> Courses[Сервис курсов]
    API --> Content[Сервис контента]
    API --> Chat[Сервис чата]
    API --> Progress[Сервис прогресса]
    
    %% Базы данных
    Auth --> UserDB[(PostgreSQL: Пользователи)]
    Courses --> CourseDB[(PostgreSQL: Курсы)]
    Content --> ContentDB[(PostgreSQL: Контент)]
    Progress --> ProgressDB[(PostgreSQL: Прогресс)]
    
    %% Redis сервисы
    Chat --> RedisChat[(Redis: Чат)]
    Courses --> RedisCache[(Redis: Кэш)]
    
    %% WebSocket
    Web --> WS[WebSocket Gateway]
    WS --> Chat
    
    %% Telegram Bot Worker
    API --> BotService[Сервис Telegram]
    BotService --> BotWorker[Воркер бота]
    BotWorker --> RedisQueue[(Redis: Очереди)]
```

## 📁 Структура проекта

```
educate/
├── Dockerfile              # Основной Dockerfile для веб-приложения
├── Dockerfile.bot          # Dockerfile для Telegram бота
├── docker-compose.yml      # Docker Compose конфигурация
├── requirements.txt        # Зависимости основного приложения
├── requirements_bot.txt    # Зависимости Telegram бота
├── .env.example           # Пример переменных окружения
├── .gitignore            # Файл исключений Git
│
├── educa/                 # Основное Django приложение
│   ├── courses/           # Модуль курсов
│   │   ├── api/           # API для курсов
│   │   │   ├── client.py          # API клиент
│   │   │   ├── serializers.py     # Сериализаторы
│   │   │   ├── urls.py            # Маршруты API
│   │   │   └── views.py           # Представления API
│   │   └── models.py      # Модели курсов
│   │
│   ├── telegram_bot/      # Модуль Telegram бота
│   │   ├── __init__.py
│   │   ├── api_client.py          # Клиент для работы с API
│   │   ├── apps.py                # Конфигурация приложения
│   │   ├── bot_runner.py          # Запуск бота
│   │   ├── config.py              # Конфигурация бота
│   │   └── main.py               # Основная логика бота
│   │
│   ├── chat/              # Модуль чата (Django Channels)
│   ├── students/          # Модуль студентов
│   └── educa/             # Настройки проекта
│       ├── settings/
│       │   ├── base.py    # Базовые настройки
│       │   ├── dev.py     # Настройки разработки
│       │   └── prod.py    # Продакшн настройки
│       └── urls.py        # Основные маршруты
│
├── data/                  # Локальные данные (в .gitignore)
│   ├── db/               # Данные PostgreSQL
│   └── cache/            # Данные Redis
│
└── docs/                 # Документация
```

## 🛠️ Установка и запуск

### Предварительные требования
- **Docker и Docker Compose**
- **Python 3.9+**
- **Telegram Bot Token** (от [@BotFather](https://t.me/botfather))

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone https://github.com/yourusername/educate.git
cd educate
```

2. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив свои настройки
```

3. **Запуск с Docker**
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

4. **Инициализация базы данных**
```bash
# Применение миграций
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

# Загрузка тестовых данных
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
```

### Локальная разработка

1. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

2. **Установка зависимостей**
```bash
pip install -r requirements.txt
pip install -r requirements_bot.txt
```

3. **Настройка переменных окружения**
```bash
export SECRET_KEY='your-secret-key'
export DATABASE_URL='postgresql://user:pass@localhost:5432/educate'
export TELEGRAM_BOT_TOKEN='your-bot-token'
```

4. **Запуск сервисов**
```bash
# Запуск Redis (для кэша и чата)
docker run -d -p 6379:6379 redis

# Запуск PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=educate postgres

# Применение миграций
python manage.py migrate

# Запуск Django сервера
python manage.py runserver

# Запуск Telegram бота (в отдельном терминале)
python -m educa.telegram_bot.bot_runner

# Запуск Daphne для WebSocket (в отдельном терминале)
daphne educa.asgi:application
```

## 🔧 Конфигурация

### Основные переменные окружения (.env)
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных
DATABASE_URL=postgresql://educate:password@db:5432/educate

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/

# Настройки SSL
SSL_ENABLED=True
```

### Конфигурация Telegram бота
```python
# educa/telegram_bot/config.py
BOT_CONFIG = {
    'token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'webhook_url': os.getenv('TELEGRAM_WEBHOOK_URL'),
    'api_base_url': 'http://web:8000/api/',
    'commands': {
        'start': 'Начать работу с ботом',
        'courses': 'Просмотреть доступные курсы',
        'progress': 'Мой прогресс обучения',
        'help': 'Помощь по командам',
    }
}
```

## 📡 API Endpoints

### Курсы
- `GET /api/courses/` - список курсов
- `GET /api/courses/{id}/` - детали курса
- `POST /api/courses/{id}/enroll/` - записаться на курс
- `GET /api/courses/{id}/contents/` - содержимое курса

### Пользователи
- `POST /api/users/register/` - регистрация
- `POST /api/users/login/` - авторизация
- `GET /api/users/me/` - профиль текущего пользователя

### Чат
- `WS /ws/chat/{room_name}/` - WebSocket для чата
- `GET /api/chat/rooms/` - список чат-комнат
- `GET /api/chat/messages/{room_id}/` - история сообщений

### Telegram Bot Webhook
- `POST /api/telegram/webhook/` - endpoint для вебхука Telegram

## 🤖 Команды Telegram бота

```
/start - Начало работы
/courses - Список доступных курсов
/my_courses - Мои курсы
/progress {course_id} - Прогресс по курсу
/notifications - Настройка уведомлений
/help - Помощь
```

## 🐳 Docker Compose сервисы

```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: educate
      POSTGRES_USER: educate
      POSTGRES_PASSWORD: educate
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
  
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    environment:
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      API_URL: http://web:8000/api/
    depends_on:
      - web
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

## 🔐 Безопасность

### Настройки безопасности в продакшн
```python
# educa/educa/settings/prod.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### SSL/TLS настройка
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://web:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📊 Мониторинг и логи

### Команды для мониторинга
```bash
# Просмотр логов Docker
docker-compose logs -f web
docker-compose logs -f bot

# Мониторинг Redis
docker-compose exec redis redis-cli monitor

# Проверка состояния базы данных
docker-compose exec db psql -U educate -d educate -c "\dt"
```

### Интеграция с Django Debug Toolbar
```python
# settings/dev.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

## 🧪 Тестирование

```bash
# Запуск тестов
docker-compose exec web python manage.py test

# Тестирование с покрытием
docker-compose exec web coverage run manage.py test
docker-compose exec web coverage report

# Запуск тестов API
docker-compose exec web python manage.py test courses.api
```

## 🚀 Развертывание

### Настройка для продакшн
1. Обновить `ALLOWED_HOSTS` в `.env`
2. Настроить SSL сертификаты
3. Настроить статические файлы:
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

4. Настроить вебхук Telegram бота:
```bash
curl -F "url=https://your-domain.com/api/telegram/webhook/" \
  https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook
```

### Масштабирование
```bash
# Масштабирование веб-серверов
docker-compose up -d --scale web=3

# Масштабирование воркеров бота
docker-compose up -d --scale bot=2
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Запушите в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request
