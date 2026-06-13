import html
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import current_user
from ..extensions import db
from ..models import Work, Review, CharityFile, Favorite

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    works = Work.query.order_by(Work.id.desc()).limit(3).all()
    return render_template('public/index.html', featured_works=works)


@public_bp.route('/portfolio')
def portfolio():
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'newest')
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 9

    query = Work.query
    if category != 'all':
        query = query.filter_by(category=category)
    if status != 'all':
        query = query.filter_by(status=status)

    query = query.order_by(Work.year.asc() if sort == 'oldest' else Work.year.desc())

    # Постраничный вывод включается только без активных фильтров -
    # при фильтрации показываются сразу все найденные работы.
    if category == 'all' and status == 'all':
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        works = pagination.items
    else:
        works = query.all()
        pagination = None

    favorite_ids = set()
    if current_user.is_authenticated:
        favorite_ids = {f.work_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}

    return render_template('public/portfolio.html', works=works,
                           # Данные работ в виде словарей передаются отдельно -
                           # шаблон превращает их в JSON для модального окна.
                           works_data=[w.to_dict() for w in works],
                           active_category=category, active_sort=sort,
                           active_status=status,
                           categories=Work.CATEGORIES,
                           pagination=pagination,
                           favorite_ids=favorite_ids)


@public_bp.route('/portfolio/favorite/<int:work_id>', methods=['POST'])
def toggle_favorite(work_id):
    if not current_user.is_authenticated:
        flash('Войдите, чтобы добавлять в избранное', 'error')
        return redirect(url_for('auth.login'))

    Work.query.get_or_404(work_id)
    existing = Favorite.query.filter_by(user_id=current_user.id, work_id=work_id).first()

    # Повторный клик снимает работу из избранного, иначе - добавляет.
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Favorite(user_id=current_user.id, work_id=work_id))

    db.session.commit()

    next_url = request.form.get('next') or url_for('public.portfolio')
    return redirect(next_url)


@public_bp.route('/about')
def about():
    return render_template('public/about.html')


@public_bp.route('/shop')
def shop():
    return render_template('public/shop.html')


@public_bp.route('/charity')
def charity():
    files = CharityFile.query.order_by(CharityFile.upload_date.desc()).all()
    return render_template('public/charity.html', files=files)


@public_bp.route('/charity/download/<int:file_id>')
def download_charity_file(file_id):
    file = CharityFile.query.get_or_404(file_id)
    # Счётчик скачиваний увеличивается при каждом обращении к файлу.
    file.download_count += 1
    db.session.commit()
    return send_from_directory(current_app.config['UPLOAD_FOLDER_CHARITY'],
                               file.filename, as_attachment=True)


@public_bp.route('/reviews')
def reviews():
    reviews_list = Review.query.filter_by(is_approved=True).order_by(Review.date.desc()).all()
    return render_template('public/reviews.html', reviews=reviews_list)


@public_bp.route('/reviews/add', methods=['POST'])
def add_review():
    if not current_user.is_authenticated:
        flash('Чтобы оставить отзыв, необходимо войти в аккаунт', 'error')
        return redirect(url_for('auth.login'))

    author = request.form.get('author', '').strip()
    text = request.form.get('text', '').strip()
    rating = request.form.get('rating', 5)

    if not author or not text:
        flash('Пожалуйста, заполните все поля', 'error')
        return redirect(url_for('public.reviews'))

    if len(text) > 1000:
        flash('Текст отзыва не должен превышать 1000 символов', 'error')
        return redirect(url_for('public.reviews'))

    # Экранирование защищает от вставки HTML/JS через текст отзыва.
    # Новый отзыв попадает на сайт только после одобрения администратором.
    review = Review(
        author=html.escape(author),
        text=html.escape(text),
        rating=int(rating),
        user_id=current_user.id,
        ip_address=request.remote_addr,
    )
    db.session.add(review)
    db.session.commit()

    flash('Спасибо за отзыв! Он будет опубликован после проверки.', 'success')
    return redirect(url_for('public.reviews'))
