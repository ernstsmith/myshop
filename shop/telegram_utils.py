import json
import urllib.parse
import urllib.request

from django.conf import settings


def send_telegram_message(text: str) -> None:
    """
    Отправляет сообщение в Telegram через Bot API.
    Использует TELEGRAM_BOT_TOKEN и TELEGRAM_ADMIN_CHAT_ID из настроек.
    Если переменные не заданы, тихо выходит.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

    if not token or not chat_id or not text:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as resp:
            # читаем ответ, чтобы не оставлять висящие соединения
            resp.read()
    except Exception:
        # не роняем оформление заказа, если Telegram недоступен
        return

