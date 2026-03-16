# shop/tests.py
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

class SettingsTests(TestCase):
    def test_debug_is_boolean(self):
        # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ DEBUG вЂ” Р±СѓР»РµРІРѕ Р·РЅР°С‡РµРЅРёРµ
        self.assertIsInstance(settings.DEBUG, bool)

    def test_secret_key_not_default(self):
        # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ SECRET_KEY РѕС‚Р»РёС‡Р°РµС‚СЃСЏ РѕС‚ "replace-me-with-env-secret"
        self.assertNotEqual(settings.SECRET_KEY, "replace-me-with-env-secret")


class ViewsTests(TestCase):
    def test_homepage_status_code(self):
        # РџСЂРѕРІРµСЂСЏРµРј РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ РіР»Р°РІРЅРѕР№ СЃС‚СЂР°РЅРёС†С‹
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])  # 302 РµСЃР»Рё РµСЃС‚СЊ СЂРµРґРёСЂРµРєС‚

    def test_gallery_page_renders(self):
        # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃС‚СЂР°РЅРёС†Р° РіР°Р»РµСЂРµРё СЂРµРЅРґРµСЂРёС‚СЃСЏ РєРѕСЂСЂРµРєС‚РЅРѕ
        response = self.client.get("/gallery/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Галерея")


class TemplateTests(TestCase):
    def test_gallery_template_exists(self):
        # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ С„Р°Р№Р» С€Р°Р±Р»РѕРЅР° gallery.html СЃСѓС‰РµСЃС‚РІСѓРµС‚
        from django.template.loader import get_template
        template = get_template("shop/gallery.html")
        self.assertIsNotNone(template)
