import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template

# Загрузка переменных окружения из .env (секретный ключ, почта и т.д.)
load_dotenv()


def create_app(config_name=None):
    # Режим работы (development/production) берётся из переменной окружения.
    # Если она не задана, используется конфигурация по умолчанию.
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # Базовая настройка логирования: уровень WARNING и выше.
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
    )

    app = Flask(__name__)

    # Конфигурация
    from .config import config
    app.config.from_object(config[config_name])

    # Убеждаемся, что папки для загрузок существуют
    os.makedirs(app.config['UPLOAD_FOLDER_PORTFOLIO'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_CHARITY'], exist_ok=True)

    # Расширения
    from .extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)

    # Страница и сообщение для неавторизованного пользователя.
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Войдите в аккаунт, чтобы продолжить'
    login_manager.login_message_category = 'error'

    from .models import User

    # Загрузка пользователя по id из сессии (требуется Flask-Login).
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from .routes.public import public_bp
    from .routes.auth import auth_bp
    from .routes.cabinet import cabinet_bp
    from .routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cabinet_bp)
    app.register_blueprint(admin_bp)

    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        # Откат транзакции, чтобы сессия БД не осталась в незавершённом состоянии.
        from .extensions import db as _db
        _db.session.rollback()
        return render_template('errors/500.html'), 500

    # Инициализация БД и создание администратора
    with app.app_context():
        from .extensions import db as _db
        _db.create_all()
        _migrate_db(_db)
        _seed_admin(app)

    return app


def _migrate_db(db):
    # Ручная миграция таблицы user: если колонок для сброса пароля ещё нет,
    # они добавляются через ALTER TABLE. Полноценный Alembic здесь избыточен.
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    user_columns = {c['name'] for c in inspector.get_columns('user')}
    new_cols = {
        'reset_token': 'VARCHAR(200)',
        'reset_token_expires': 'DATETIME',
    }
    with db.engine.connect() as conn:
        for col, col_type in new_cols.items():
            if col not in user_columns:
                conn.execute(text(f'ALTER TABLE user ADD COLUMN {col} {col_type}'))
        conn.commit()


def _seed_admin(app):
    # Если в базе нет ни одного администратора, создаётся учётная запись
    # с дефолтным паролем. Пароль обязательно меняется после первого входа.
    from .extensions import db
    from .models import User

    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
        )
        admin.set_password('CHANGE_THIS_PASSWORD_NOW!')
        db.session.add(admin)
        db.session.commit()

        print('=' * 55)
        print('  Администратор создан!')
        print('  Логин:   admin')
        print('  Пароль:  CHANGE_THIS_PASSWORD_NOW!')
        print('  Панель:  /admin/')
        print('=' * 55)
