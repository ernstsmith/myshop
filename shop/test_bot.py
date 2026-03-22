import json
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from django.test import RequestFactory

from shop import bot
from shop.views import api_create_order


def _make_update(user_id=42):
    message = SimpleNamespace(reply_text=AsyncMock(), web_app_data=None)
    effective_user = SimpleNamespace(id=user_id, username="tester")
    return SimpleNamespace(message=message, effective_user=effective_user, callback_query=None)


def _make_context(admin_chat_id=123456, webapp_url="https://myshop-production-2acb.up.railway.app/miniapp/"):
    app = SimpleNamespace(bot_data={"admin_chat_id": admin_chat_id, "webapp_url": webapp_url})
    bot_mock = SimpleNamespace(send_message=AsyncMock())
    return SimpleNamespace(application=app, bot=bot_mock)


class BotConfigTests(TestCase):
    def test_get_bot_config_loads_env_values(self):
        token, admin_chat_id = bot.get_bot_config(
            {
                "TELEGRAM_BOT_TOKEN": "token-value",
                "TELEGRAM_ADMIN_CHAT_ID": "987654321",
            }
        )
        self.assertEqual(token, "token-value")
        self.assertEqual(admin_chat_id, 987654321)


class OrderApiTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_create_order_via_api(self):
        request = self.factory.post(
            "/api/order/",
            data=json.dumps(
                {
                    "user_id": 42,
                    "username": "tester",
                    "product": "Tea",
                    "quantity": 2,
                }
            ),
            content_type="application/json",
        )

        with patch("shop.views.Order.objects.create", return_value=SimpleNamespace(id=101)) as create_mock:
            response = api_create_order(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content), {"status": "ok", "order_id": 101})
        create_mock.assert_called_once_with(
            user_id=42,
            username="tester",
            product="Tea",
            quantity=2,
            total_amount=0,
        )


class BotHandlersTests(IsolatedAsyncioTestCase):
    async def test_start_command_replies_welcome_message(self):
        update = _make_update()
        context = _make_context()

        await bot.start(update, context)

        update.message.reply_text.assert_awaited_once_with("Добро пожаловать в магазин 👕")

    async def test_test_command_sends_message_to_admin_chat(self):
        update = _make_update()
        context = _make_context(admin_chat_id=777)

        await bot.test(update, context)

        context.bot.send_message.assert_awaited_once_with(
            chat_id=777,
            text="Тестовое сообщение 🚀",
        )
        update.message.reply_text.assert_awaited_once_with("Сообщение отправлено")

    async def test_shop_command_returns_webapp_button(self):
        webapp_url = "https://myshop-production-2acb.up.railway.app/miniapp/"
        update = _make_update()
        context = _make_context(webapp_url=webapp_url)

        await bot.shop(update, context)

        update.message.reply_text.assert_awaited_once()
        args, kwargs = update.message.reply_text.await_args
        self.assertEqual(args[0], "Нажмите кнопку, чтобы открыть магазин")
        markup = kwargs["reply_markup"]
        button = markup.inline_keyboard[0][0]
        self.assertEqual(button.web_app.url, webapp_url)

    async def test_handle_miniapp_data_parses_payload_and_creates_order(self):
        update = _make_update()
        update.message.web_app_data = SimpleNamespace(
            data='{"telegram_user_id":42,"telegram_username":"tester","product":"Tea","quantity":2}'
        )
        context = _make_context()

        with patch("shop.bot._post_order_to_api", return_value=True) as post_order_mock:
            await bot.handle_miniapp_data(update, context)

        post_order_mock.assert_called_once_with(
            "http://localhost:8000/api/order/",
            {"user_id": 42, "username": "tester", "product": "Tea", "quantity": 2},
        )
        update.message.reply_text.assert_awaited_once_with("Заказ принят ✅")

    async def test_handle_miniapp_data_sends_admin_notification(self):
        update = _make_update()
        update.message.web_app_data = SimpleNamespace(
            data='{"telegram_user_id":42,"telegram_username":"tester","product":"Tea","quantity":2}'
        )
        context = _make_context()

        with patch("shop.bot._post_order_to_api", return_value=True):
            await bot.handle_miniapp_data(update, context)

        context.bot.send_message.assert_awaited_once_with(
            chat_id=123456,
            text=(
                "🛒 Новый заказ\n\n"
                "Пользователь: @tester\n"
                "ID: 42\n\n"
                "Товар: Tea\n"
                "Количество: 2"
            ),
        )

    async def test_handle_miniapp_data_handles_invalid_json(self):
        update = _make_update()
        update.message.web_app_data = SimpleNamespace(data="not-json")
        context = _make_context()

        await bot.handle_miniapp_data(update, context)

        update.message.reply_text.assert_awaited_once_with("Получены некорректные данные из Mini App")

    async def test_handle_miniapp_data_handles_api_error(self):
        update = _make_update()
        update.message.web_app_data = SimpleNamespace(
            data='{"telegram_user_id":42,"telegram_username":"tester","product":"Tea","quantity":2}'
        )
        context = _make_context()

        with patch("shop.bot._post_order_to_api", return_value=False):
            await bot.handle_miniapp_data(update, context)

        update.message.reply_text.assert_awaited_once_with("Не удалось оформить заказ")
