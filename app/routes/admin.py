import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import User, Work, Review, CharityFile
from ..utils import allowed_file, save_file, get_file_size, get_file_type

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    # Для не-администратора возвращается 404, а не 403 - так раздел
    # /admin не выдаёт своё существование посторонним пользователям.
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(404)
        return f(*args, **kwargs)
    return decorated


# ── Дашборд ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html',
                           works_count=Work.query.count(),
                           reviews_count=Review.query.count(),
                           reviews_pending=Review.query.filter_by(is_approved=False).count(),
                           charity_count=CharityFile.query.count(),
                           users_count=User.query.filter_by(role='user').count())


# ── Работы ───────────────────────────────────────────────────────────────────

@admin_bp.route('/works')
@login_required
@admin_required
def works():
    all_works = Work.query.order_by(Work.year.desc()).all()
    return render_template('admin/works.html', works=all_works, categories=Work.CATEGORIES)


@admin_bp.route('/works/add', methods=['POST'])
@login_required
@admin_required
def work_add():
    # Изображение опционально - работу можно создать и без него.
    image_path = ''
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        if not allowed_file(file):
            flash('Недопустимый формат изображения', 'error')
            return redirect(url_for('admin.works'))
        folder = current_app.config['UPLOAD_FOLDER_PORTFOLIO']
        image_path = save_file(file, folder)

    price_raw = request.form.get('price', '')
    work = Work(
        title=request.form.get('title'),
        technique=request.form.get('technique'),
        size=request.form.get('size'),
        year=int(request.form.get('year', 0)),
        category=request.form.get('category'),
        image_path=image_path,
        status=request.form.get('status', 'not-for-sale'),
        price=int(price_raw) if price_raw.strip() else None,
        description=request.form.get('description', ''),
    )
    db.session.add(work)
    db.session.commit()
    flash('Работа добавлена', 'success')
    return redirect(url_for('admin.works'))


@admin_bp.route('/works/edit/<int:work_id>', methods=['POST'])
@login_required
@admin_required
def work_edit(work_id):
    work = Work.query.get_or_404(work_id)

    # Новое изображение загружается только если выбран файл -
    # иначе старое image_path остаётся без изменений.
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        if allowed_file(file):
            folder = current_app.config['UPLOAD_FOLDER_PORTFOLIO']
            work.image_path = save_file(file, folder)

    price_raw = request.form.get('price', '')
    work.title = request.form.get('title', work.title)
    work.technique = request.form.get('technique', work.technique)
    work.size = request.form.get('size', work.size)
    work.year = int(request.form.get('year', work.year))
    work.category = request.form.get('category', work.category)
    work.status = request.form.get('status', work.status)
    work.price = int(price_raw) if price_raw.strip() else None
    work.description = request.form.get('description', work.description)
    db.session.commit()
    flash('Работа обновлена', 'success')
    return redirect(url_for('admin.works'))


@admin_bp.route('/works/delete/<int:work_id>')
@login_required
@admin_required
def work_delete(work_id):
    work = Work.query.get_or_404(work_id)
    # Файл изображения удаляется вместе с записью, чтобы не оставались
    # "осиротевшие" файлы в папке загрузок.
    if work.image_path:
        path = os.path.join(current_app.config['UPLOAD_FOLDER_PORTFOLIO'], work.image_path)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(work)
    db.session.commit()
    flash('Работа удалена', 'success')
    return redirect(url_for('admin.works'))


# ── Отзывы ───────────────────────────────────────────────────────────────────

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    all_reviews = Review.query.order_by(Review.date.desc()).all()
    return render_template('admin/reviews.html', reviews=all_reviews)


@admin_bp.route('/reviews/approve/<int:review_id>')
@login_required
@admin_required
def review_approve(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    db.session.commit()
    flash('Отзыв одобрен', 'success')
    return redirect(url_for('admin.reviews'))


@admin_bp.route('/reviews/delete/<int:review_id>')
@login_required
@admin_required
def review_delete(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Отзыв удалён', 'success')
    return redirect(url_for('admin.reviews'))


# ── Благотворительность ───────────────────────────────────────────────────────

@admin_bp.route('/charity')
@login_required
@admin_required
def charity():
    files = CharityFile.query.order_by(CharityFile.upload_date.desc()).all()
    return render_template('admin/charity.html', files=files)


@admin_bp.route('/charity/upload', methods=['POST'])
@login_required
@admin_required
def charity_upload():
    if 'file' not in request.files or not request.files['file'].filename:
        flash('Файл не выбран', 'error')
        return redirect(url_for('admin.charity'))

    file = request.files['file']
    if not allowed_file(file):
        flash('Недопустимый формат файла. Разрешены: PDF, PNG, JPG, JPEG, GIF', 'error')
        return redirect(url_for('admin.charity'))

    # Оригинальное имя файла сохраняется отдельно для отображения пользователю,
    # а на диске файл хранится под именем, сгенерированным save_file().
    folder = current_app.config['UPLOAD_FOLDER_CHARITY']
    original_name = file.filename
    file_size = get_file_size(file)
    filename = save_file(file, folder)

    charity_file = CharityFile(
        title=request.form.get('title'),
        description=request.form.get('description'),
        filename=filename,
        original_filename=original_name,
        file_type=get_file_type(filename),
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.session.add(charity_file)
    db.session.commit()
    flash('Файл успешно загружен', 'success')
    return redirect(url_for('admin.charity'))


@admin_bp.route('/charity/delete/<int:file_id>')
@login_required
@admin_required
def charity_delete(file_id):
    f = CharityFile.query.get_or_404(file_id)
    # Файл на диске удаляется вместе с записью в базе.
    path = os.path.join(current_app.config['UPLOAD_FOLDER_CHARITY'], f.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(f)
    db.session.commit()
    flash('Файл удалён', 'success')
    return redirect(url_for('admin.charity'))


# ── Пользователи ──────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/block/<int:user_id>')
@login_required
@admin_required
def user_block(user_id):
    user = User.query.get_or_404(user_id)
    # Повторное нажатие переключает блокировку обратно.
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = 'заблокирован' if user.is_blocked else 'разблокирован'
    flash(f'Пользователь {user.username} {status}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён', 'success')
    return redirect(url_for('admin.users'))
