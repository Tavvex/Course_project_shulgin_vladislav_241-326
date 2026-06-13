from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Объекты создаются здесь без привязки к приложению и инициализируются
# позже через init_app() в create_app() - так избегаются циклические импорты.
db = SQLAlchemy()
login_manager = LoginManager()
