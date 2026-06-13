import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_reset_email(to_email, reset_url):
    # Учётные данные почты задаются через .env - если они не настроены
    # (или остались placeholder-значения), письмо не отправляется.
    from_email = os.environ.get('ALERT_EMAIL_FROM', '')
    password = os.environ.get('ALERT_EMAIL_PASSWORD', '')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    if not from_email or 'your-email' in from_email or not password:
        return False

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = 'Сброс пароля — Мошурова Полина'
    msg.attach(MIMEText(
        f'Вы запросили сброс пароля.\n\n'
        f'Перейдите по ссылке для создания нового пароля:\n{reset_url}\n\n'
        f'Ссылка действительна 1 час.\n\n'
        f'Если вы не запрашивали сброс пароля — проигнорируйте это письмо.',
        'plain', 'utf-8',
    ))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception:
        # Ошибка отправки не должна ломать запрос пользователя -
        # форма просто сообщит, что письмо не отправлено.
        return False
