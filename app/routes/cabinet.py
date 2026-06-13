import html
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from ..extensions import db
from ..models import User, Review, Favorite

cabinet_bp = Blueprint('cabinet', __name__, url_prefix='/cabinet')


@cabinet_bp.route('/profile')
@login_required
def profile():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('cabinet/profile.html', favorites=favorites)


@cabinet_bp.route('/edit', methods=['POST'])
@login_required
def edit():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    new_password = request.form.get('new_password', '')
    current_password = request.form.get('current_password', '')

    # Любое изменение профиля требует подтверждения текущим паролем.
    if not current_user.check_password(current_password):
        flash('Неверный текущий пароль', 'error')
        return redirect(url_for('cabinet.profile'))

    if username and username != current_user.username:
        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'error')
            return redirect(url_for('cabinet.profile'))
        current_user.username = username

    if email and email != current_user.email:
        if User.query.filter_by(email=email).first():
            flash('Этот email уже занят', 'error')
            return redirect(url_for('cabinet.profile'))
        current_user.email = email

    if new_password:
        if len(new_password) < 6:
            flash('Новый пароль должен содержать минимум 6 символов', 'error')
            return redirect(url_for('cabinet.profile'))
        current_user.set_password(new_password)

    db.session.commit()
    flash('Профиль успешно обновлён', 'success')
    return redirect(url_for('cabinet.profile'))


# ── Управление отзывами ──────────────────────────────────────────────────────

@cabinet_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    # Удалить отзыв может только его автор.
    if review.user_id != current_user.id:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash('Отзыв удалён', 'success')
    return redirect(url_for('cabinet.profile'))


@cabinet_bp.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        abort(403)

    text = request.form.get('text', '').strip()
    rating = request.form.get('rating', review.rating)

    if not text:
        flash('Текст отзыва не может быть пустым', 'error')
        return redirect(url_for('cabinet.profile'))
    if len(text) > 1000:
        flash('Текст отзыва не должен превышать 1000 символов', 'error')
        return redirect(url_for('cabinet.profile'))

    # После редактирования отзыв снова уходит на модерацию.
    review.text = html.escape(text)
    review.rating = int(rating)
    review.is_approved = False
    db.session.commit()
    flash('Отзыв обновлён и отправлен на повторную проверку', 'success')
    return redirect(url_for('cabinet.profile'))
