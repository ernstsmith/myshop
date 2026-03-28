import re

with open('shop/views.py', 'r') as f:
    content = f.read()

# Ищем функцию home и добавляем CLOUDINARY_CLOUD_NAME
old = """    return render(request, 'shop/home.html', {
        'products': products,
        'gallery_images': gallery_images
    })"""

new = """    return render(request, 'shop/home.html', {
        'products': products,
        'gallery_images': gallery_images,
        'CLOUDINARY_CLOUD_NAME': settings.CLOUDINARY_CLOUD_NAME,
    })"""

content = content.replace(old, new)

with open('shop/views.py', 'w') as f:
    f.write(content)

print("✅ home view исправлена")
