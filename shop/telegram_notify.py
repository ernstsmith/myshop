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


def notify_order_status(order):
    if not TOKEN:
        return
    telegram_user = order.telegram_user
    if not telegram_user or not telegram_user.telegram_id:
        return

    text = (
        f"Статус вашего заказа №{order.id} изменен: "
        f"{order.get_status_display()}"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": telegram_user.telegram_id,
        "text": text,
    }

    try:
        requests.post(url, json=data, timeout=5)
    except requests.RequestException:
        return
