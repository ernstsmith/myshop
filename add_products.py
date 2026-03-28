import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import Product

products_data = [
    {'id': 1, 'title': 'Худи', 'price': 2500, 'image': 'products/ChatGPT_Image_10_мар._2026_г._21_27_49.png', 'slug': 'khudi'},
    {'id': 2, 'title': 'Футболка polo Graffiti', 'price': 1500, 'image': 'products/ChatGPT_Image_10_мар._2026_г._21_27_42.png', 'slug': 'futbolka-polo-graffiti'},
    {'id': 3, 'title': 'Лонгслив Street Style', 'price': 2000, 'image': 'products/ChatGPT_Image_9_мар_xWxzpqn._2026_г._18_40_47.png', 'slug': 'longsiv-street-style'},
    {'id': 4, 'title': 'Майка', 'price': 1200, 'image': 'products/ChatGPT_Image_10_мар._2026_г._21_28_24.png', 'slug': 'majka'},
]

for p in products_data:
    obj, created = Product.objects.update_or_create(
        id=p['id'],
        defaults={
            'title': p['title'],
            'price': p['price'],
            'image': p['image'],
            'slug': p['slug'],
            'available': True,
            'description': ''
        }
    )
    print(f"{'✅ Добавлен' if created else '🔄 Обновлён'}: {p['title']}")

print(f"\n📊 Всего товаров в БД: {Product.objects.count()}")
