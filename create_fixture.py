import os
import sys
import django

sys.path.append('/mnt/c/Users/erikm/myshop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')

try:
    django.setup()
    from shop.models import Product
    import json
    
    products = Product.objects.all()
    data = []
    
    for p in products:
        data.append({
            "model": "shop.product",
            "pk": p.id,
            "fields": {
                "title": p.title,
                "slug": p.slug,
                "description": p.description or "",
                "price": str(p.price),
                "image": p.image,
                "available": p.available
            }
        })
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создана фикстура с {len(data)} товарами")
    
except Exception as e:
    print(f"Ошибка: {e}")
