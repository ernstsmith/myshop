import hashlib
import hmac
import json
import logging
import time
import urllib.parse
import urllib.request

from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

keyboard = [
    [
        InlineKeyboardButton(
            "Открыть магазин",
            web_app=WebAppInfo(url="https://xxxxx.ngrok-free.dev")
        )
    ]
]

reply_markup = InlineKeyboardMarkup(keyboard)

logger = logging.getLogger(__name__)


def send_telegram_message(text: str) -> None:
    """
    Отправляет сообщение в Telegram через Bot API.
    Использует TELEGRAM_BOT_TOKEN и TELEGRAM_ADMIN_CHAT_ID из настроек.
    Если переменные не заданы, тихо выходит.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

    if not text:
        return

    if not token or not chat_id:
        logger.error(
            "Telegram settings missing: TELEGRAM_BOT_TOKEN=%s TELEGRAM_ADMIN_CHAT_ID=%s",
            "set" if token else "missing",
            "set" if chat_id else "missing",
        )
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

def get_telegram_user(request):
    init_data = request.GET.get("initData")
    return init_data


def verify_telegram_init_data(init_data: str, token: str, max_age_seconds: int = 86400) -> bool:
    if not init_data or not token:
        return False

    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    except ValueError:
        return False

    received_hash = data.pop("hash", None)
    if not received_hash:
        return False

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return False

    if max_age_seconds and "auth_date" in data:
        try:
            auth_date = int(data["auth_date"])
        except (TypeError, ValueError):
            return False

        now = int(time.time())
        if now - auth_date > max_age_seconds:
            return False

    return True
