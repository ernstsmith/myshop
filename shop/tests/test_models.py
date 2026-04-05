from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from shop.models import (
    Cart,
    CartItem,
    DeliveryAddress,
    Order,
    OrderItem,
    Product,
    TelegramUser,
    UserProfile,
)


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.base_product = Product.objects.create(
            title="Base Product",
            slug="base-product",
            price=Decimal("1.00"),
        )

    def test_product_creation(self):
        product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("9.99"),
        )
        self.assertEqual(product.title, "Test Product")
        self.assertEqual(product.price, Decimal("9.99"))
        self.assertTrue(product.available)

    def test_product_str(self):
        product = Product.objects.create(
            title="Awesome Item",
            slug="awesome-item",
            price=Decimal("19.99"),
        )
        self.assertEqual(str(product), "Awesome Item")

    def test_product_required_fields(self):
        product = Product()
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_slug_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                title="Dup",
                slug="base-product",
                price=Decimal("2.00"),
            )

    def test_product_price_non_negative_validation(self):
        product = Product(title="Bad", slug="bad", price=Decimal("-1.00"))
        with self.assertRaises(ValidationError):
            product.full_clean()


class CartModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.decimal_product = Product.objects.create(
            title="Decimal Item",
            slug="decimal-item",
            price=Decimal("0.10"),
        )
        cls.base_user = TelegramUser.objects.create(
            telegram_id="tg-1",
            auth_date=timezone.now(),
        )

    def setUp(self):
        self.product = Product.objects.create(
            title="Widget",
            slug="widget",
            price=Decimal("5.00"),
        )
        self.telegram_user = TelegramUser.objects.create(
            telegram_id="12345",
            auth_date=timezone.now(),
        )

    def test_cart_creation(self):
        cart = Cart.objects.create(telegram_user=self.telegram_user)
        self.assertEqual(cart.telegram_user, self.telegram_user)

    def test_cart_get_total(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart.get_total(), Decimal("10.00"))

    def test_cart_to_order(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.product, quantity=3)

        order = cart.to_order(
            telegram_user=self.telegram_user,
            telegram_user_id="tg-123",
            username="tester",
        )

        self.assertEqual(order.telegram_user, self.telegram_user)
        self.assertEqual(order.tg_user_id, "tg-123")
        self.assertEqual(order.tg_username, "tester")
        self.assertEqual(order.total_amount, Decimal("15.00"))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(cart.items.count(), 0)
        self.assertEqual(order.metadata.get("cart_id"), cart.id)

    def test_cart_get_total_empty(self):
        cart = Cart.objects.create()
        self.assertEqual(cart.get_total(), 0)

    def test_cart_to_order_empty(self):
        cart = Cart.objects.create()
        order = cart.to_order(telegram_user=self.base_user)
        self.assertEqual(order.total_amount, 0)
        self.assertEqual(order.items.count(), 0)
        self.assertEqual(cart.items.count(), 0)

    def test_cart_decimal_precision(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.decimal_product, quantity=3)
        self.assertEqual(cart.get_total(), Decimal("0.30"))

    def test_cart_to_order_moves_items_and_total(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=cart, product=self.decimal_product, quantity=3)

        order = cart.to_order(telegram_user=self.base_user)

        self.assertEqual(cart.items.count(), 0)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_amount, Decimal("10.30"))


class CartItemModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Gadget",
            slug="gadget",
            price=Decimal("7.50"),
        )

    def setUp(self):
        self.cart = Cart.objects.create()

    def test_cart_item_creation(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product, self.product)

    def test_cart_item_str(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=4)
        self.assertEqual(str(item), "Gadget × 4")

    def test_cart_item_unique_together(self):
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_cart_item_negative_quantity_validation(self):
        item = CartItem(cart=self.cart, product=self.product, quantity=-1)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_cart_item_required_fields(self):
        item = CartItem()
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_cart_item_deleted_on_product_delete(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.product.delete()
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Item",
            slug="item",
            price=Decimal("2.50"),
        )
        cls.decimal_product = Product.objects.create(
            title="Tiny",
            slug="tiny",
            price=Decimal("0.10"),
        )

    def setUp(self):
        self.product = self.__class__.product

    def test_order_creation(self):
        order = Order.objects.create()
        self.assertEqual(order.status, Order.STATUS_NEW)
        self.assertFalse(order.paid)

    def test_order_str(self):
        order = Order.objects.create(total_amount=Decimal("12.34"))
        self.assertIn("Order #", str(order))
        self.assertIn("12.34", str(order))

    def test_order_calculate_total(self):
        order = Order.objects.create()
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=4,
            price=Decimal("2.50"),
        )
        total = order.calculate_total()
        self.assertEqual(total, Decimal("10.00"))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("10.00"))

    def test_order_calculate_total_empty(self):
        order = Order.objects.create()
        total = order.calculate_total()
        self.assertEqual(total, 0)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, 0)

    def test_order_decimal_precision(self):
        order = Order.objects.create()
        OrderItem.objects.create(
            order=order,
            product=self.decimal_product,
            quantity=3,
            price=Decimal("0.10"),
        )
        total = order.calculate_total()
        self.assertEqual(total, Decimal("0.30"))

    def test_order_str_contains_id_and_total(self):
        order = Order.objects.create(total_amount=Decimal("5.00"))
        text = str(order)
        self.assertIn(str(order.id), text)
        self.assertIn("5.00", text)


class OrderItemModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Part",
            slug="part",
            price=Decimal("3.00"),
        )

    def setUp(self):
        self.order = Order.objects.create()
        self.product = self.__class__.product

    def test_order_item_creation(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=Decimal("3.00"),
        )
        self.assertEqual(item.get_total(), Decimal("6.00"))

    def test_order_item_str(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=5,
            price=Decimal("3.00"),
        )
        self.assertEqual(str(item), "Part × 5")

    def test_order_item_required_fields(self):
        item = OrderItem(order=self.order, product=self.product)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_order_item_negative_price_validation(self):
        item = OrderItem(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("-1.00"),
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_order_item_get_total_precision(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price=Decimal("0.10"),
        )
        self.assertEqual(item.get_total(), Decimal("0.30"))

    def test_order_items_deleted_on_order_delete(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("3.00"),
        )
        self.order.delete()
        self.assertFalse(OrderItem.objects.filter(pk=item.pk).exists())

    def test_product_delete_protected_by_order_item(self):
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("3.00"),
        )
        with self.assertRaises(ProtectedError):
            self.product.delete()


class TelegramUserModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.base_user = TelegramUser.objects.create(
            telegram_id="999",
            username="tg_user",
            auth_date=timezone.now(),
        )

    def test_telegram_user_creation(self):
        user = TelegramUser.objects.create(
            telegram_id="998",
            username="tg_user",
            auth_date=timezone.now(),
        )
        self.assertEqual(user.telegram_id, "998")

    def test_telegram_user_str_username(self):
        user = TelegramUser.objects.create(
            telegram_id="111",
            username="handle",
            auth_date=timezone.now(),
        )
        self.assertEqual(str(user), "handle")

    def test_telegram_user_str_name_fallback(self):
        user = TelegramUser.objects.create(
            telegram_id="222",
            first_name="John",
            last_name="Doe",
            auth_date=timezone.now(),
        )
        self.assertEqual(str(user), "John Doe")

    def test_telegram_user_required_fields(self):
        user = TelegramUser()
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_telegram_user_unique_telegram_id(self):
        with self.assertRaises(IntegrityError):
            TelegramUser.objects.create(
                telegram_id="999",
                auth_date=timezone.now(),
            )

    def test_telegram_user_str_fallback_id(self):
        user = TelegramUser.objects.create(
            telegram_id="333",
            auth_date=timezone.now(),
        )
        self.assertEqual(str(user), "TelegramUser 333")


class UserProfileModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="user_base", password="pass")

    def test_user_profile_creation(self):
        user = User.objects.create_user(username="user1", password="pass")
        profile = UserProfile.objects.create(user=user, phone="12345")
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.phone, "12345")

    def test_user_profile_str(self):
        user = User.objects.create_user(username="user2", password="pass")
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(str(profile), f"Profile for {user}")

    def test_user_profile_required_fields(self):
        profile = UserProfile()
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_user_profile_deleted_with_user(self):
        profile = UserProfile.objects.create(user=self.user)
        self.user.delete()
        self.assertFalse(UserProfile.objects.filter(pk=profile.pk).exists())


class DeliveryAddressModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="addr_user", password="pass")

    def test_delivery_address_creation(self):
        user = User.objects.create_user(username="user3", password="pass")
        address = DeliveryAddress.objects.create(
            user=user,
            name="Home",
            city="Moscow",
            street="Main St",
            postal_code="123456",
        )
        self.assertEqual(address.user, user)

    def test_delivery_address_str(self):
        user = User.objects.create_user(username="user4", password="pass")
        address = DeliveryAddress.objects.create(
            user=user,
            name="Office",
            city="SPB",
            street="Nevsky",
            postal_code="654321",
        )
        self.assertEqual(str(address), "Office (SPB)")

    def test_delivery_address_required_fields(self):
        address = DeliveryAddress()
        with self.assertRaises(ValidationError):
            address.full_clean()

    def test_delivery_address_deleted_with_user(self):
        address = DeliveryAddress.objects.create(
            user=self.user,
            name="Home",
            city="Moscow",
            street="Main St",
            postal_code="123456",
        )
        self.user.delete()
        self.assertFalse(DeliveryAddress.objects.filter(pk=address.pk).exists())
