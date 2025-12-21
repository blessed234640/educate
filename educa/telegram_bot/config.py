import os

class Config:
    @property
    def TELEGRAM_TOKEN(self):
        return os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    @property
    def API_BASE_URL(self):
        return os.getenv('API_BASE_URL', 'https://ethically-polished-brill.cloudpub.ru/api')
    
    @property
    def SITE_URL(self):
        return os.getenv('SITE_URL', 'https://ethically-polished-brill.cloudpub.ru')
    
    # Параметры пагинации
    PAGE_SIZE = 5
    MAX_COURSES_PER_PAGE = 5

config = Config()