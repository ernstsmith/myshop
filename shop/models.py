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

    def to_order(self, telegram_user_id=None):
        """
        Создаёт заказ на основе текущей корзины и очищает корзину.
        """
        with transaction.atomic():
            total_amount = self.get_total()

            # Создаём заказ
            order = Order.objects.create(
                telegram_user_id=telegram_user_id,
                total_amount=total_amount,
                paid=False,
                metadata={"cart_id": self.id}
            )

            # Переносим все элементы корзины в заказ
            for item in self.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price  # фиксируем цену на момент заказа
                )

            # Очищаем корзину
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
    created_at = models.DateTimeField(auto_now_add=True)
    telegram_user_id = models.CharField(max_length=64, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        status = "Оплачен" if self.paid else "Не оплачен"
        return f"Заказ #{self.id} — {self.total_amount} ₽ ({status})"


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

    def __str__(self):
        total_price = self.price * self.quantity
        return f"{self.product.title} × {self.quantity} — {total_price} ₽"