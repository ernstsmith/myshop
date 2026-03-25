from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created:
        # Здесь код при создании заказа
        pass
