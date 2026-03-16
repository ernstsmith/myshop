from django.db import models, transaction
from decimal import Decimal


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return sum(
            item.product.price * item.quantity
            for item in self.items.all()
        )

    def to_order(self, telegram_user_id=None, username=""):
        """
        Создаёт заказ на основе корзины
        """
        with transaction.atomic():

            order = Order.objects.create(
                telegram_user_id=telegram_user_id,
                username=username,
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
    STATUS_CONFIRMED = "confirmed"
    STATUS_SENT = "sent"
    STATUS_CANCELED = "canceled"

    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_CONFIRMED, "Подтвержден"),
        (STATUS_SENT, "Отправлен"),
        (STATUS_CANCELED, "Отменен"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)

    telegram_user_id = models.CharField(max_length=64, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, default="")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"