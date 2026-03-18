from django.db import migrations, models


def forwards(apps, schema_editor):
    Order = apps.get_model("shop", "Order")
    mapping = {
        "confirmed": "processing",
        "sent": "shipped",
        "canceled": "cancelled",
    }
    for old_status, new_status in mapping.items():
        Order.objects.filter(status=old_status).update(status=new_status)


def backwards(apps, schema_editor):
    Order = apps.get_model("shop", "Order")
    mapping = {
        "processing": "confirmed",
        "shipped": "sent",
        "cancelled": "canceled",
    }
    for old_status, new_status in mapping.items():
        Order.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0009_rename_order_telegram_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "Новый"),
                    ("processing", "В обработке"),
                    ("shipped", "Отправлен"),
                    ("delivered", "Доставлен"),
                    ("cancelled", "Отменен"),
                ],
                default="new",
                max_length=20,
            ),
        ),
    ]
