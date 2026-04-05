from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase

from shop import bot
from shop.models import Order


class BotConfigExtraTests(TestCase):
    def test_get_bot_config_missing_token(self):
        with self.assertRaises(ValueError):
            bot.get_bot_config({"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_ADMIN_CHAT_ID": "1"})

    def test_get_bot_config_missing_admin(self):
        with self.assertRaises(ValueError):
            bot.get_bot_config({"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_ADMIN_CHAT_ID": ""})

    def test_get_bot_config_invalid_admin(self):
        with self.assertRaises(ValueError):
            bot.get_bot_config({"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_ADMIN_CHAT_ID": "x"})

    def test_get_admin_chat_id_from_context(self):
        app = SimpleNamespace(bot_data={"admin_chat_id": 99})
        context = SimpleNamespace(application=app)
        self.assertEqual(bot._get_admin_chat_id(context), 99)

    def test_get_webapp_url_from_context(self):
        app = SimpleNamespace(bot_data={"webapp_url": "https://example.com"})
        context = SimpleNamespace(application=app)
        self.assertEqual(bot._get_webapp_url(context), "https://example.com")

    def test_get_order_api_url_from_env(self):
        with patch.dict("os.environ", {"ORDER_API_URL": "http://api.local/order"}):
            self.assertEqual(bot._get_order_api_url(SimpleNamespace(application=None)), "http://api.local/order")

    def test_post_order_to_api_failure(self):
        with patch("shop.bot.urllib.request.urlopen", side_effect=bot.urllib.error.URLError("fail")):
            self.assertFalse(bot._post_order_to_api("http://api", {"a": 1}))

    def test_post_order_to_api_success(self):
        fake_response = MagicMock()
        fake_response.status = 201
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = None
        with patch("shop.bot.urllib.request.urlopen", return_value=fake_response):
            self.assertTrue(bot._post_order_to_api("http://api", {"a": 1}))


class BotHandlersExtraTests(IsolatedAsyncioTestCase):
    async def test_handle_miniapp_data_missing_items(self):
        update = SimpleNamespace(
            message=SimpleNamespace(reply_text=AsyncMock(), web_app_data=SimpleNamespace(data='{"x":1}')),
            effective_user=SimpleNamespace(id=1, username="u"),
        )
        context = SimpleNamespace(application=None, bot=SimpleNamespace(send_message=AsyncMock()))

        await bot.handle_miniapp_data(update, context)

        update.message.reply_text.assert_awaited_once_with("Получены некорректные данные из Mini App")

    async def test_handle_order_buttons_invalid_data(self):
        query = SimpleNamespace(data="bad", answer=AsyncMock(), edit_message_text=AsyncMock())
        update = SimpleNamespace(callback_query=query)
        await bot.handle_order_buttons(update, SimpleNamespace())
        query.answer.assert_awaited_once_with("Некорректные данные")

    async def test_handle_order_buttons_unknown_action(self):
        query = SimpleNamespace(data="unknown_1", answer=AsyncMock(), edit_message_text=AsyncMock())
        update = SimpleNamespace(callback_query=query)
        await bot.handle_order_buttons(update, SimpleNamespace())
        query.answer.assert_awaited_once_with("Неизвестное действие")

    async def test_handle_order_buttons_order_not_found(self):
        query = SimpleNamespace(data="confirm_999", answer=AsyncMock(), edit_message_text=AsyncMock())
        update = SimpleNamespace(callback_query=query)
        with patch("shop.models.Order.objects.get", side_effect=Order.DoesNotExist):
            await bot.handle_order_buttons(update, SimpleNamespace())
        query.answer.assert_awaited_once_with("Заказ не найден")

    async def test_handle_order_buttons_updates_status(self):
        fake_order = SimpleNamespace(
            id=1,
            status=Order.STATUS_NEW,
            get_status_display=lambda: "В обработке",
            save=lambda *args, **kwargs: None,
        )
        query = SimpleNamespace(data="confirm_1", answer=AsyncMock(), edit_message_text=AsyncMock())
        update = SimpleNamespace(callback_query=query)
        with patch("shop.models.Order.objects.get", return_value=fake_order):
            await bot.handle_order_buttons(update, SimpleNamespace())

        self.assertEqual(fake_order.status, Order.STATUS_PROCESSING)
        query.answer.assert_awaited_once_with("Статус обновлен")
        query.edit_message_text.assert_awaited_once()
