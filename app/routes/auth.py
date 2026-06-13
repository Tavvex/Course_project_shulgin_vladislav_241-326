from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.is_blocked:
            flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'error')
            return render_template('auth/login.html')

        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            # Администратор сразу попадает в панель управления,
            # обычный пользователь - на страницу, с которой пришёл (или на главную).
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('public.index'))

        flash('Неверное имя пользователя или пароль', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not username or not email or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('auth/register.html')

        if password != password_confirm:
            flash('Пароли не совпадают', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email, role='user')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Добро пожаловать! Регистрация прошла успешно.', 'success')
        return redirect(url_for('public.index'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('public.index'))


# ── Сброс пароля ─────────────────────────────────────────────────────────────

def _make_serializer():
    # Подписанный токен на основе SECRET_KEY - подделать его без ключа нельзя,
    # а срок действия проверяется при загрузке (см. reset_password).
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = _make_serializer().dumps(user.email, salt='pwd-reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            from ..mail import send_reset_email
            send_reset_email(user.email, reset_url)

        # Сообщение одинаковое независимо от того, найден email или нет -
        # так нельзя проверить по ответу, зарегистрирован ли адрес.
        flash('Если аккаунт с таким email существует, инструкции отправлены на него.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    # Токен действителен 1 час с момента создания (max_age в секундах).
    try:
        email = _make_serializer().loads(token, salt='pwd-reset', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('Ссылка для сброса пароля недействительна или устарела.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != password_confirm:
            flash('Пароли не совпадают', 'error')
            return render_template('auth/reset_password.html', token=token)

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Пароль успешно изменён. Войдите с новым паролем.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
