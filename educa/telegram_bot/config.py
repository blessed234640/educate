import os

class Config:
    # Из вашего settings.py
    TELEGRAM_TOKEN = "8553270096:AAF6P9wlhzrtx-zcrOO77J5uUS7BoTS_d3g"
    API_BASE_URL = "http://localhost:8000/api"
    SITE_URL = "http://localhost:8000"  # URL вашего сайта
    
    # Параметры API
    PAGE_SIZE = 5  # Курсов на страницу

config = Config()