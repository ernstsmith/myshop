import hashlib
import hmac
import json
import os
import tempfile
import time
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.functional import empty
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.models import Cart, CartItem, Order, OrderItem, Product, TelegramUser, UserProfile


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        staticfiles_storage._wrapped = empty

    def test_home_without_gallery_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=tmpdir):
                response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("gallery_images", response.context)

    def test_home_with_gallery_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gallery_dir = os.path.join(tmpdir, "static", "gallery")
            os.makedirs(gallery_dir, exist_ok=True)
            with open(os.path.join(gallery_dir, "a.jpg"), "wb") as f:
                f.write(b"x")
            with open(os.path.join(gallery_dir, "b.txt"), "wb") as f:
                f.write(b"x")
            with override_settings(BASE_DIR=tmpdir):
                response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("gallery_images", response.context)
        self.assertEqual(response.context["gallery_images"], ["gallery/a.jpg"])

    def test_product_detail(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        response = self.client.get(reverse("product_detail", args=[product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["product"], product)

    def test_cart_view_with_session_cart(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        session = self.client.session
        session["cart"] = {str(product.id): 2}
        session.save()

        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], Decimal("20.00"))

    def test_cart_view_loads_from_db_for_telegram_user(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        telegram_user = TelegramUser.objects.create(
            telegram_id="100",
            auth_date=timezone.now(),
        )
        cart = Cart.objects.create(telegram_user=telegram_user)
        CartItem.objects.create(cart=cart, product=product, quantity=3)

        session = self.client.session
        session["telegram_user_pk"] = telegram_user.pk
        session["cart"] = {}
        session.save()

        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], Decimal("30.00"))

    def test_add_to_cart_updates_db_cart(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        telegram_user = TelegramUser.objects.create(
            telegram_id="101",
            auth_date=timezone.now(),
        )

        session = self.client.session
        session["telegram_user_pk"] = telegram_user.pk
        session.save()

        response = self.client.post(reverse("add_to_cart", args=[product.id]))
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(telegram_user=telegram_user)
        self.assertEqual(cart.items.count(), 1)

    def test_remove_from_cart_updates_db_cart(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        telegram_user = TelegramUser.objects.create(
            telegram_id="102",
            auth_date=timezone.now(),
        )
        cart = Cart.objects.create(telegram_user=telegram_user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        session = self.client.session
        session["telegram_user_pk"] = telegram_user.pk
        session["cart_db_id"] = cart.id
        session["cart"] = {str(product.id): 1}
        session.save()

        response = self.client.post(reverse("remove_from_cart", args=[product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_checkout_get(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        session = self.client.session
        session["cart"] = {str(product.id): 1}
        session.save()

        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], Decimal("10.00"))

    def test_checkout_post_creates_order_and_clears_cart(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        telegram_user = TelegramUser.objects.create(
            telegram_id="200",
            auth_date=timezone.now(),
        )
        cart = Cart.objects.create(telegram_user=telegram_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        session = self.client.session
        session["telegram_user_pk"] = telegram_user.pk
        session["cart"] = {str(product.id): 2}
        session["cart_db_id"] = cart.id
        session.save()

        response = self.client.post(reverse("checkout"), data={"telegram_user_id": telegram_user.telegram_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_price, Decimal("20.00"))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

        session = self.client.session
        self.assertEqual(session.get("cart"), {})
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

    def test_login_view(self):
        with override_settings(TELEGRAM_BOT_USERNAME="botname"):
            response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("telegram_auth_url", response.context)

    def test_profile_redirects_when_anonymous(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_shows_orders(self):
        user = User.objects.create_user(username="u1", password="pass")
        telegram_user = TelegramUser.objects.create(
            telegram_id="300",
            auth_date=timezone.now(),
        )
        UserProfile.objects.create(user=user, telegram_user=telegram_user)
        Order.objects.create(telegram_user=telegram_user)

        self.client.force_login(user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["orders"]), 1)

    def test_update_order_status_invalid(self):
        staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        order = Order.objects.create()
        self.client.force_login(staff)

        response = self.client.post(
            reverse("update_order_status", args=[order.id]),
            data={"status": "bad"},
        )
        self.assertEqual(response.status_code, 400)

    def test_update_order_status_valid(self):
        staff = User.objects.create_user(username="staff2", password="pass", is_staff=True)
        order = Order.objects.create()
        self.client.force_login(staff)

        response = self.client.post(
            reverse("update_order_status", args=[order.id]),
            data={"status": Order.STATUS_PROCESSING},
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PROCESSING)

    def _build_hash(self, token, data):
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hashlib.sha256(token.encode("utf-8")).digest()
        return hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def test_verify_telegram_auth_invalid_method(self):
        response = self.client.post(reverse("telegram_auth"))
        self.assertEqual(response.status_code, 400)

    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_verify_telegram_auth_missing_token(self):
        response = self.client.get(reverse("telegram_auth"))
        self.assertEqual(response.status_code, 400)

    @override_settings(TELEGRAM_BOT_TOKEN="token")
    def test_verify_telegram_auth_missing_hash(self):
        response = self.client.get(reverse("telegram_auth"), data={"id": "1"})
        self.assertEqual(response.status_code, 400)

    @override_settings(TELEGRAM_BOT_TOKEN="token")
    def test_verify_telegram_auth_invalid_hash(self):
        response = self.client.get(reverse("telegram_auth"), data={"id": "1", "hash": "bad"})
        self.assertEqual(response.status_code, 403)

    @override_settings(TELEGRAM_BOT_TOKEN="token")
    def test_verify_telegram_auth_expired(self):
        auth_date = int(time.time()) - 999999
        data = {"id": "1", "auth_date": auth_date}
        data["hash"] = self._build_hash("token", data)
        response = self.client.get(reverse("telegram_auth"), data=data)
        self.assertEqual(response.status_code, 403)

    @override_settings(TELEGRAM_BOT_TOKEN="token")
    def test_verify_telegram_auth_valid(self):
        auth_date = int(time.time())
        data = {"id": "1", "auth_date": auth_date, "username": "test"}
        data["hash"] = self._build_hash("token", data)
        response = self.client.get(reverse("telegram_auth"), data=data)
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session.get("telegram_user_id"), "1")

    def test_api_create_order_method_not_allowed(self):
        response = self.client.get(reverse("api_create_order"))
        self.assertEqual(response.status_code, 405)

    def test_api_create_order_empty_cart(self):
        response = self.client.post(
            reverse("api_create_order"),
            data=json.dumps({"cart": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_create_order_success(self):
        product = Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        response = self.client.post(
            reverse("api_create_order"),
            data=json.dumps({"cart": [{"id": product.id, "quantity": 2}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["total"], 20.0)

    def test_api_create_order_invalid_product(self):
        response = self.client.post(
            reverse("api_create_order"),
            data=json.dumps({"cart": [{"id": 999, "quantity": 1}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)

    def test_api_products_fallback(self):
        response = self.client.get(reverse("api_products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_api_products_with_data(self):
        Product.objects.all().delete()
        Product.objects.create(title="Tea", slug="tea", price=Decimal("10.00"))
        response = self.client.get(reverse("api_products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_misc_pages(self):
        for name in ["gallery", "privacy_policy", "cookie_policy", "terms", "miniapp", "vk_miniapp"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_debug_and_health(self):
        response = self.client.get(reverse("debug_version"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("debug_function"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
