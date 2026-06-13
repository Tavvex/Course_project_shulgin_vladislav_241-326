from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Хранится только хеш пароля, сам пароль никогда не сохраняется.
    password_hash = db.Column(db.String(200), nullable=False)
    # 'user' или 'admin' - роль определяет доступ к /admin.
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    # Поля для защиты от подбора пароля.
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    is_blocked = db.Column(db.Boolean, default=False)
    # Токен и срок действия для восстановления пароля по email.
    reset_token = db.Column(db.String(200))
    reset_token_expires = db.Column(db.DateTime)

    reviews = db.relationship('Review', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True,
                                cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def increment_attempts(self):
        # Вызывается после неудачного входа - используется для блокировки аккаунта.
        self.login_attempts += 1
        db.session.commit()

    def reset_attempts(self):
        # Сбрасывает счётчик неудачных попыток входа и снимает блокировку.
        self.login_attempts = 0
        self.locked_until = None
        db.session.commit()


class Work(db.Model):
    # Работа художника, отображаемая в портфолио.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    technique = db.Column(db.String(100))
    size = db.Column(db.String(50))
    year = db.Column(db.Integer)
    category = db.Column(db.String(50))
    image_path = db.Column(db.String(200))
    # 'for-sale' или 'not-for-sale'.
    status = db.Column(db.String(20), default='not-for-sale')
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    favorites = db.relationship('Favorite', backref='work', lazy=True,
                                cascade='all, delete-orphan')

    # Список категорий для фильтров на странице портфолио и в админке.
    CATEGORIES = [
        ('portrait', 'Портреты'),
        ('still-life', 'Натюрморты'),
        ('landscape', 'Пейзажи'),
        ('sketches', 'Этюды'),
        ('free-composition', 'Свободная композиция'),
    ]

    def to_dict(self):
        # Используется для передачи данных о работе в шаблон как JSON
        # (модальное окно с подробностями на странице портфолио).
        return {
            'id': self.id,
            'title': self.title,
            'technique': self.technique,
            'size': self.size,
            'year': self.year,
            'category': self.category,
            'image_path': self.image_path,
            'status': self.status,
            'price': self.price,
            'description': self.description,
        }


class Favorite(db.Model):
    # Связь "пользователь - избранная работа".
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('work.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Одну и ту же работу нельзя добавить в избранное дважды.
    __table_args__ = (db.UniqueConstraint('user_id', 'work_id'),)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    # Может быть пустым, если отзыв оставлен без привязки к аккаунту.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    # Отзыв появляется на сайте только после одобрения администратором.
    is_approved = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))

    @property
    def formatted_date(self):
        return self.date.strftime('%d.%m.%Y %H:%M')


class CharityFile(db.Model):
    # Файл из благотворительного раздела (документ, изображение и т.п.).
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Имя файла на диске (генерируется при сохранении, не совпадает с оригинальным).
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200))
    file_type = db.Column(db.String(10))
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
