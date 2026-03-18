import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")


def send_order_notification(order):

    items = ""
    for item in order.items.all():
        items += f"{item.product.title} × {item.quantity}\n"

    text = (
        f"🛒 <b>Новый заказ #{order.id}</b>\n\n"
        f"{items}\n"
        f"💰 Сумма: {order.total_amount} ₽"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": f"confirm_{order.id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{order.id}"}
            ],
            [
                {"text": "📦 Отправлен", "callback_data": f"sent_{order.id}"}
            ]
        ]
    }

    data = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    }

    try:
        requests.post(url, json=data, timeout=5)
    except requests.RequestException:
        return
