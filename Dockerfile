# взять официальный базовый Docker образ Python 
from python:3.12.3


# Задать переменные среды
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Задать рабочий каталог
WORKDIR /code


#Установить зависимости
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# копируется джанго проект
COPY . .

# Создание пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /code
USER botuser

# Запуск бота
CMD ["python", "-m", "telegram_bot.main"]