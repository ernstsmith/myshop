import hashlib
import hmac
import time
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase, override_settings

from shop import telegram_utils


class TelegramUtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_send_telegram_message_no_text(self):
        with patch("shop.telegram_utils.urllib.request.urlopen") as urlopen_mock:
            telegram_utils.send_telegram_message("")
        urlopen_mock.assert_not_called()

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_ADMIN_CHAT_ID="")
    def test_send_telegram_message_missing_settings(self):
        with patch("shop.telegram_utils.urllib.request.urlopen") as urlopen_mock:
            telegram_utils.send_telegram_message("Hello")
        urlopen_mock.assert_not_called()

    @override_settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_ADMIN_CHAT_ID=123)
    def test_send_telegram_message_success(self):
        fake_response = MagicMock()
        fake_response.read.return_value = b"ok"
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = None

        with patch("shop.telegram_utils.urllib.request.urlopen", return_value=fake_response) as urlopen_mock:
            telegram_utils.send_telegram_message("Hello")

        urlopen_mock.assert_called_once()

    def test_get_telegram_user(self):
        request = self.factory.get("/?initData=abc123")
        self.assertEqual(telegram_utils.get_telegram_user(request), "abc123")

    def _build_init_data(self, token, data):
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hmac.new(
            b"WebAppData",
            token.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        payload = data.copy()
        payload["hash"] = signature
        return "&".join(f"{k}={v}" for k, v in payload.items())

    def test_verify_telegram_init_data_success(self):
        token = "token"
        data = {"auth_date": int(time.time()), "user": "42"}
        init_data = self._build_init_data(token, data)
        self.assertTrue(telegram_utils.verify_telegram_init_data(init_data, token))

    def test_verify_telegram_init_data_missing_hash(self):
        self.assertFalse(telegram_utils.verify_telegram_init_data("user=1", "token"))

    def test_verify_telegram_init_data_bad_hash(self):
        self.assertFalse(telegram_utils.verify_telegram_init_data("user=1&hash=bad", "token"))

    def test_verify_telegram_init_data_expired(self):
        token = "token"
        old_time = int(time.time()) - 999999
        init_data = self._build_init_data(token, {"auth_date": old_time, "user": "42"})
        self.assertFalse(
            telegram_utils.verify_telegram_init_data(init_data, token, max_age_seconds=10)
        )
