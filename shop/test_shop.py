# shop/tests.py
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

class SettingsTests(TestCase):
    def test_debug_is_boolean(self):
        # Проверяем, что DEBUG — булево значение
        self.assertIsInstance(settings.DEBUG, bool)

    def test_secret_key_not_default(self):
        # Проверяем, что SECRET_KEY отличается от "replace-me-with-env-secret"
        self.assertNotEqual(settings.SECRET_KEY, "replace-me-with-env-secret")


class ViewsTests(TestCase):
    def test_homepage_status_code(self):
        # Проверяем доступность главной страницы
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])  # 302 если есть редирект

    def test_gallery_page_renders(self):
        # Проверяем, что страница галереи рендерится корректно
        response = self.client.get("/gallery/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery")


class TemplateTests(TestCase):
    def test_gallery_template_exists(self):
        # Проверяем, что файл шаблона gallery.html существует
        from django.template.loader import get_template
        template = get_template("shop/gallery.html")
        self.assertIsNotNone(template)