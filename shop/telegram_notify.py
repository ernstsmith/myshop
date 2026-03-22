import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")


def send_order_notification(order, items_list):
    from django.conf import settings
    import requests
    
    total = sum(item['subtotal'] for item in items_list)
    
    # Формируем сообщение
    message = f"🛍 *Новый заказ #{order.id}*\n\n"
    message += "📦 *Товары:*\n"
    for item in items_list:
        message += f"• {item['title']} x{item['quantity']} = {item['subtotal']} ₽\n"
    message += f"\n💰 *Итого:* {total} ₽"
    
    if order.telegram_user:
        message += f"\n👤 *Покупатель:* @{order.telegram_user.username or 'user'}"
    
    # Отправляем администратору
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if admin_chat_id:
        requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                'chat_id': admin_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
        )


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
