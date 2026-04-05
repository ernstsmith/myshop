from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    telegram_user = models.ForeignKey(
        "TelegramUser",
        related_name="carts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def get_total(self):
        return sum(
            item.product.price * item.quantity
            for item in self.items.all()
        )

    def to_order(self, telegram_user=None, telegram_user_id=None, username=""):
        """
        Создаёт заказ на основе корзины
        """
        with transaction.atomic():

            order = Order.objects.create(
                telegram_user=telegram_user,
                tg_user_id=telegram_user_id,
                tg_username=username,
                total_amount=self.get_total(),
                paid=False,
                metadata={"cart_id": self.id}
            )

            for item in self.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            self.items.all().delete()

            return order


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


class Order(models.Model):

    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_SHIPPED, "Отправлен"),
        (STATUS_DELIVERED, "Доставлен"),
        (STATUS_CANCELLED, "Отменен"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)

    telegram_user = models.ForeignKey(
        "TelegramUser",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    tg_user_id = models.CharField(max_length=64, blank=True, null=True)
    tg_username = models.CharField(max_length=150, blank=True, default="")

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    paid = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )

    metadata = models.JSONField(default=dict, blank=True)

    def calculate_total(self):
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = total
        self.save()
        return total

    def __str__(self):
        return f"Order #{self.id} — {self.total_amount} ₽"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


class TelegramUser(models.Model):
    telegram_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=150, blank=True, default="")
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    photo_url = models.URLField(blank=True, default="")
    auth_date = models.DateTimeField()

    def __str__(self):
        display = self.username or f"{self.first_name} {self.last_name}".strip()
        return display or f"TelegramUser {self.telegram_id}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    telegram_user = models.OneToOneField(
        "TelegramUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"Profile for {self.user}"


class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    apartment = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.city})"
