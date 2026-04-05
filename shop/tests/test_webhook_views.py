import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse


class WebhookViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_telegram_webhook_get(self):
        response = self.client.get("/webhook/")
        self.assertEqual(response.status_code, 200)

    def test_telegram_webhook_post_invalid_json(self):
        with patch("shop.webhook_views.threading.Thread") as thread_mock:
            response = self.client.post("/webhook/", data="not-json", content_type="application/json")
        self.assertEqual(response.status_code, 200)
        thread_mock.assert_not_called()
