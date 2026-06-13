import os
import secrets

# Папка с пакетом приложения - все пути ниже строятся относительно неё,
# чтобы конфигурация не зависела от текущей рабочей директории.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Если SECRET_KEY не задан в окружении, генерируется случайный
    # (на каждый перезапуск свой - подходит только для разработки).
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # По умолчанию используется локальная SQLite-база в app/database/site.db.
    # Для продакшена путь переопределяется переменной DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'site.db')
    ).replace('postgres://', 'postgresql://')
    # Куда сохраняются загруженные изображения работ и файлы благотворительности
    # (раздел charity может содержать не только изображения, но и PDF,
    # поэтому он хранится отдельно от static/images).
    UPLOAD_FOLDER_PORTFOLIO = os.path.join(BASE_DIR, 'static', 'images', 'portfolio')
    UPLOAD_FOLDER_CHARITY = os.path.join(BASE_DIR, 'static', 'uploads', 'charity')
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
    # Ограничение размера загружаемого файла - 16 МБ.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Куки сессии передаются только по HTTPS и недоступны из JS.
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


# Используется в create_app() для выбора конфигурации по имени окружения.
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
