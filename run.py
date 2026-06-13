from app import create_app

app = create_app()

if __name__ == '__main__':
    # Waitress используется как production-сервер; если он не установлен,
    # запускается встроенный сервер Flask (только для разработки).
    try:
        from waitress import serve
        print('Сервер запущен: http://127.0.0.1:5000')
        serve(app, host='127.0.0.1', port=5000, threads=8)
    except ImportError:
        app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)