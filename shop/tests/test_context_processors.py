from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from django.utils import timezone

from shop.context_processors import telegram_user
from shop.models import TelegramUser


class TelegramUserContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _add_session(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_returns_none_when_session_missing(self):
        request = self._add_session(self.factory.get("/"))
        data = telegram_user(request)
        self.assertIsNone(data["telegram_user"])
        self.assertIn("CLOUDINARY_CLOUD_NAME", data)

    def test_clears_missing_user(self):
        request = self._add_session(self.factory.get("/"))
        request.session["telegram_user_pk"] = 999
        request.session.save()

        data = telegram_user(request)
        self.assertIsNone(data["telegram_user"])
        self.assertIsNone(request.session.get("telegram_user_pk"))

    def test_returns_user_when_present(self):
        user = TelegramUser.objects.create(
            telegram_id="10",
            auth_date=timezone.now(),
        )
        request = self._add_session(self.factory.get("/"))
        request.session["telegram_user_pk"] = user.pk
        request.session.save()

        data = telegram_user(request)
        self.assertEqual(data["telegram_user"], user)
