import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Сигнатуры (магические байты) в начале файла - по ним проверяется,
# что содержимое действительно соответствует заявленному расширению.
FILE_SIGNATURES = {
    'pdf': [b'%PDF'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'gif': [b'GIF87a', b'GIF89a'],
}


def allowed_file(file):
    # Проверка загруженного файла: расширение из белого списка
    # и соответствие сигнатуры реальному формату файла.
    if not file or not file.filename:
        return False
    if '.' not in file.filename:
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    return _check_signature(file, ext)


def _check_signature(file, ext):
    # Считывается начало файла и сравнивается с известными сигнатурами.
    # Указатель чтения возвращается в начало, чтобы файл можно было
    # сохранить целиком дальше.
    data = file.read(256)
    file.seek(0)
    for sig in FILE_SIGNATURES.get(ext, []):
        if data.startswith(sig):
            return True
    return ext not in FILE_SIGNATURES


def save_file(file, upload_folder):
    # Имя файла на диске формируется из даты/времени загрузки и исходного
    # имени - так исключаются коллизии и сохраняется читаемость.
    os.makedirs(upload_folder, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    name = secure_filename(file.filename.rsplit('.', 1)[0])
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}.{ext}"
    file.save(os.path.join(upload_folder, filename))
    return filename


def get_file_size(file):
    # Размер определяется через перемещение указателя в конец файла,
    # после чего указатель возвращается обратно в начало.
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size


def get_file_type(filename):
    # Для отображения в карточке файла: PDF отдельно, остальное - изображение.
    ext = filename.rsplit('.', 1)[1].lower()
    return 'pdf' if ext == 'pdf' else 'image'
