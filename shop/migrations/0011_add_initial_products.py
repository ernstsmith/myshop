from django.db import migrations

def add_products(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    products = [
        (1, 'Худи', 2500, 'products/ChatGPT_Image_10_мар._2026_г._21_27_49.png', 'khudi'),
        (2, 'Футболка polo Graffiti', 1500, 'products/ChatGPT_Image_10_мар._2026_г._21_27_42.png', 'futbolka-polo-graffiti'),
        (3, 'Лонгслив Street Style', 2000, 'products/ChatGPT_Image_9_мар_xWxzpqn._2026_г._18_40_47.png', 'longsiv-street-style'),
        (4, 'Майка', 1200, 'products/ChatGPT_Image_10_мар._2026_г._21_28_24.png', 'majka'),
    ]
    for pid, title, price, image, slug in products:
        Product.objects.update_or_create(
            id=pid,
            defaults={
                'title': title,
                'price': price,
                'image': image,
                'slug': slug,
                'available': True,
                'description': ''
            }
        )
    print(f"Добавлено товаров: {Product.objects.count()}")

class Migration(migrations.Migration):
    dependencies = [('shop', '0010_update_order_status_choices')]
    operations = [migrations.RunPython(add_products)]
