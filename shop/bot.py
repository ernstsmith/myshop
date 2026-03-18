import json
import logging
import os
import urllib.error
import urllib.request
import urllib.parse
from typing import Mapping, Tuple

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DEFAULT_WEBAPP_URL = "https://chromatolytic-christoper-phalangeal.ngrok-free.dev/miniapp/"
DEFAULT_ORDER_API_URL = "http://localhost:8000/api/order/"


def get_bot_config(env: Mapping[str, str] | None = None) -> Tuple[str, int]:
    source = env if env is not None else os.environ
    token = source.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_chat_id_raw = source.get("TELEGRAM_ADMIN_CHAT_ID", "").strip()

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан")

    if not admin_chat_id_raw:
        raise ValueError("TELEGRAM_ADMIN_CHAT_ID не задан")

    try:
        admin_chat_id = int(admin_chat_id_raw)
    except ValueError as exc:
        raise ValueError("TELEGRAM_ADMIN_CHAT_ID должен быть целым числом") from exc

    return token, admin_chat_id


def _get_user_id(update: Update) -> int | None:
    if update.effective_user:
        return update.effective_user.id
    return None


def _get_admin_chat_id(context: ContextTypes.DEFAULT_TYPE) -> int:
    app = getattr(context, "application", None)
    if app and isinstance(app.bot_data.get("admin_chat_id"), int):
        return app.bot_data["admin_chat_id"]

    _, admin_chat_id = get_bot_config()
    return admin_chat_id


def _get_webapp_url(context: ContextTypes.DEFAULT_TYPE) -> str:
    app = getattr(context, "application", None)
    if app and isinstance(app.bot_data.get("webapp_url"), str):
        return app.bot_data["webapp_url"]
    return os.environ.get("TELEGRAM_WEBAPP_URL", DEFAULT_WEBAPP_URL).strip() or DEFAULT_WEBAPP_URL


def _get_order_api_url(context: ContextTypes.DEFAULT_TYPE) -> str:
    app = getattr(context, "application", None)
    if app and isinstance(app.bot_data.get("order_api_url"), str):
        return app.bot_data["order_api_url"]
    return os.environ.get("ORDER_API_URL", DEFAULT_ORDER_API_URL).strip() or DEFAULT_ORDER_API_URL


def _post_order_to_api(order_api_url: str, payload: dict) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        order_api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError):
        logger.exception("Failed to post order to API: %s", order_api_url)
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Incoming command /start from user_id=%s", _get_user_id(update))

    if not update.message:
        return

    webapp_url = _get_webapp_url(context)

    keyboard = [
        [InlineKeyboardButton("🛒 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]
    ]

    await update.message.reply_text(
        "Добро пожаловать в магазин 👕",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Incoming command /test from user_id=%s", _get_user_id(update))

    if not update.message:
        return

    try:
        admin_chat_id = _get_admin_chat_id(context)
    except ValueError:
        logger.exception("Bot config error while processing /test")
        await update.message.reply_text("Ошибка конфигурации бота")
        return

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text="Тестовое сообщение 🚀",
    )
    await update.message.reply_text("Сообщение отправлено")


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Incoming command /shop from user_id=%s", _get_user_id(update))

    if not update.message:
        return

    webapp_url = _get_webapp_url(context)

    keyboard = [
        [InlineKeyboardButton("🛒 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]
    ]

    await update.message.reply_text(
        "Нажмите кнопку, чтобы открыть магазин",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_miniapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.web_app_data:
        return

    try:
        logger.info("MiniApp data received: %s", update.message.web_app_data.data)
        payload = json.loads(update.message.web_app_data.data)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Invalid web_app_data payload: %r", update.message.web_app_data.data)
        await update.message.reply_text("Получены некорректные данные из Mini App")
        return

    telegram_user_id = payload.get("telegram_user_id")
    if telegram_user_id is None and update.effective_user:
        telegram_user_id = update.effective_user.id

    telegram_username = payload.get("telegram_username")
    if not telegram_username and update.effective_user:
        telegram_username = getattr(update.effective_user, "username", "") or ""

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        await update.message.reply_text("Получены некорректные данные из Mini App")
        return

    try:
        telegram_user_id = int(telegram_user_id)
    except (TypeError, ValueError):
        await update.message.reply_text("Получены некорректные данные из Mini App")
        return

    sanitized_items = []
    for item in items:
        if not isinstance(item, dict):
            await update.message.reply_text("Получены некорректные данные из Mini App")
            return
        try:
            product_id = int(item.get("id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            await update.message.reply_text("Получены некорректные данные из Mini App")
            return
        if quantity <= 0:
            await update.message.reply_text("Получены некорректные данные из Mini App")
            return
        sanitized_items.append(
            {
                "id": product_id,
                "title": str(item.get("title", "")).strip(),
                "quantity": quantity,
            }
        )

    order_payload = {
        "items": sanitized_items,
        "telegram_user_id": telegram_user_id,
        "username": str(telegram_username or "").strip(),
        "init_data": str(payload.get("init_data", "") or "").strip(),
    }
    order_api_url = _get_order_api_url(context)
    is_ok = _post_order_to_api(order_api_url, order_payload)

    if is_ok:
        admin_chat_id = _get_admin_chat_id(context)
        lines = ["🛒 Новый заказ", ""]
        lines.append(f"Пользователь: @{order_payload['username']}")
        lines.append(f"ID: {order_payload['telegram_user_id']}")
        lines.append("")
        lines.append("Товары:")
        for item in sanitized_items:
            title = item.get("title") or f"#{item['id']}"
            lines.append(f"- {title} × {item['quantity']}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text="\n".join(lines),
        )
        await update.message.reply_text("Заказ принят ✅")
    else:
        await update.message.reply_text("Не удалось оформить заказ")


async def handle_order_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        action, order_id = query.data.split("_", maxsplit=1)
    except ValueError:
        await query.answer("Некорректные данные")
        return

    if action not in {"confirm", "cancel", "sent"}:
        await query.answer("Неизвестное действие")
        return

    from shop.models import Order

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        await query.answer("Заказ не найден")
        return

    if action == "confirm":
        order.status = Order.STATUS_PROCESSING
    elif action == "cancel":
        order.status = Order.STATUS_CANCELLED
    else:
        order.status = Order.STATUS_SHIPPED

    order.save()
    await query.answer("Статус обновлен")
    await query.edit_message_text(f"Заказ #{order.id}\nСтатус: {order.get_status_display()}")


def build_application(env: Mapping[str, str] | None = None) -> Application:
    token, admin_chat_id = get_bot_config(env)
    source = env if env is not None else os.environ
    webapp_url = source.get("TELEGRAM_WEBAPP_URL", DEFAULT_WEBAPP_URL).strip() or DEFAULT_WEBAPP_URL
    order_api_url = source.get("ORDER_API_URL", DEFAULT_ORDER_API_URL).strip() or DEFAULT_ORDER_API_URL

    app = Application.builder().token(token).build()
    app.bot_data["admin_chat_id"] = admin_chat_id
    app.bot_data["webapp_url"] = webapp_url
    app.bot_data["order_api_url"] = order_api_url

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CallbackQueryHandler(handle_order_buttons))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_miniapp_data))
    return app


def run_bot() -> None:
    app = build_application()
    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
