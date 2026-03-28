import os
import sys
import django

# Добавляем путь к проекту
sys.path.append('/mnt/c/Users/erikm/myshop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')

try:
    django.setup()
    from shop.models import Product
    count = Product.objects.filter(available=True).count()
    print(f'Товаров в БД: {count}')
except Exception as e:
    print(f'Ошибка: {e}')
