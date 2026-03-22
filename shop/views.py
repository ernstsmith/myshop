import os
import json
import hashlib
import hmac
import time
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from shop.models import Product, Order, OrderItem, TelegramUser, Cart, CartItem
from shop.telegram_utils import verify_telegram_init_data
from shop.telegram_notify import notify_order_status

TELEGRAM_AUTH_MAX_AGE_SECONDS = 86400


def _get_session_telegram_user(request):
    user_pk = request.session.get("telegram_user_pk")
    if not user_pk:
        return None
    try:
        return TelegramUser.objects.get(pk=user_pk)
    except TelegramUser.DoesNotExist:
        request.session.pop("telegram_user_pk", None)
        return None

# Главная страница с товарами + динамическая галерея
def home(request):
    products = Product.objects.filter(available=True)

    # Папка gallery внутри static/
    gallery_dir = os.path.join(settings.BASE_DIR, "static", "gallery")

    if not os.path.exists(gallery_dir):
        gallery_images = []
    else:
        gallery_images = [
            f"gallery/{f}"
            for f in os.listdir(gallery_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

    return render(request, 'shop/home.html', {
        'products': products,
        'gallery_images': gallery_images
    })

# VK Mini App
def vk_miniapp(request):
    from django.conf import settings
    products = Product.objects.filter(available=True)
    return render(request, 'shop/vk_miniapp.html', {
        'products': products,
        'vk_app_id': getattr(settings, 'VK_APP_ID', '54499010'),
        'CLOUDINARY_CLOUD_NAME': getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'daqsvvw0g'),
    })

# shop/views.py

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


# Просмотр корзины
def cart_view(request):
    cart = request.session.get('cart', {})
    telegram_user = _get_session_telegram_user(request)
    if telegram_user and not cart:
        cart_obj = Cart.objects.filter(telegram_user=telegram_user).order_by("-created_at").first()
        if cart_obj:
            cart = {str(item.product_id): item.quantity for item in cart_obj.items.all()}
            request.session["cart"] = cart
            request.session["cart_db_id"] = cart_obj.id
    products = []
    total = Decimal("0")

    if cart:
        product_ids = [int(pid) for pid in cart.keys()]
        product_map = {
            product.id: product
            for product in Product.objects.filter(id__in=product_ids)
        }

        for product_id, quantity in cart.items():
            product = product_map.get(int(product_id))
            if not product:
                continue
            quantity = int(quantity)
            subtotal = product.price * quantity
            products.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
            total += subtotal
    return render(request, 'shop/cart.html', {'products': products, 'total': total})

# Добавление товара в корзину
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_key = str(product_id)
    cart[product_key] = cart.get(product_key, 0) + 1
    request.session['cart'] = cart
    telegram_user = _get_session_telegram_user(request)
    if telegram_user:
        cart_obj = None
        cart_db_id = request.session.get("cart_db_id")
        if cart_db_id:
            cart_obj = Cart.objects.filter(id=cart_db_id, telegram_user=telegram_user).first()
        if not cart_obj:
            cart_obj = Cart.objects.create(telegram_user=telegram_user)
            request.session["cart_db_id"] = cart_obj.id
        cart_item, _ = CartItem.objects.get_or_create(cart=cart_obj, product=product)
        cart_item.quantity = cart[product_key]
        cart_item.save(update_fields=["quantity"])
    return redirect('cart')

# Удаление товара из корзины
@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_key = str(product_id)
    if product_key in cart:
        del cart[product_key]
        request.session['cart'] = cart
    telegram_user = _get_session_telegram_user(request)
    if telegram_user:
        cart_db_id = request.session.get("cart_db_id")
        if cart_db_id:
            cart_obj = Cart.objects.filter(id=cart_db_id, telegram_user=telegram_user).first()
            if cart_obj:
                CartItem.objects.filter(cart=cart_obj, product_id=product_id).delete()
    return redirect('cart')

# Оформление заказа
def checkout(request):
    cart = request.session.get('cart', {})
    telegram_user = _get_session_telegram_user(request)
    if request.method == 'POST':
        total = Decimal("0")
        telegram_user_id = request.POST.get('telegram_user_id', '').strip()
        order = Order.objects.create(
            telegram_user=telegram_user,
            tg_user_id=telegram_user_id or (telegram_user.telegram_id if telegram_user else None),
            tg_username=telegram_user.username if telegram_user else "",
            total_amount=0,
            paid=False,
        )

        product_ids = [int(pid) for pid in cart.keys()]
        product_map = {
            product.id: product
            for product in Product.objects.filter(id__in=product_ids)
        }

        order_items = []
        for product_id, quantity in cart.items():
            product = product_map.get(int(product_id))
            if not product:
                continue
            quantity = int(quantity)
            subtotal = product.price * quantity
            total += subtotal
            order_items.append(
                OrderItem(order=order, product=product, quantity=quantity, price=product.price)
            )

        if order_items:
            OrderItem.objects.bulk_create(order_items)

        order.total_amount = total
        order.save(update_fields=["total_amount"])

        request.session['cart'] = {}  # очищаем корзину
        cart_db_id = request.session.pop("cart_db_id", None)
        if telegram_user and cart_db_id:
            cart_obj = Cart.objects.filter(id=cart_db_id, telegram_user=telegram_user).first()
            if cart_obj:
                cart_obj.items.all().delete()
        return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        products = []
        total = Decimal("0")

        if cart:
            product_ids = [int(pid) for pid in cart.keys()]
            product_map = {
                product.id: product
                for product in Product.objects.filter(id__in=product_ids)
            }

            for product_id, quantity in cart.items():
                product = product_map.get(int(product_id))
                if not product:
                    continue
                quantity = int(quantity)
                subtotal = product.price * quantity
                products.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
                total += subtotal
        return render(
            request,
            'shop/checkout.html',
            {'products': products, 'total': total, 'telegram_user': telegram_user},
        )

def products_page(request):
    products = Product.objects.all()
    return render(request, 'shop/products_page.html', {'products': products})

def gallery(request):
    return render(request, 'shop/gallery.html')

@xframe_options_exempt
def miniapp(request):
    return render(request, "miniapp.html")


def login(request):
    auth_url = request.build_absolute_uri(reverse("telegram_auth"))
    return render(
        request,
        "shop/login.html",
        {
            "telegram_bot_username": settings.TELEGRAM_BOT_USERNAME,
            "telegram_auth_url": auth_url,
        },
    )


def profile(request):
    telegram_user = _get_session_telegram_user(request)
    if not telegram_user:
        return redirect("/login/")

    orders = Order.objects.filter(telegram_user=telegram_user).order_by("-created_at")
    return render(
        request,
        "shop/profile.html",
        {"telegram_user": telegram_user, "orders": orders},
    )


@staff_member_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = (request.POST.get("status") or "").strip()
    allowed_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
    if new_status not in allowed_statuses:
        return HttpResponseBadRequest("Invalid status")

    if order.status != new_status:
        order.status = new_status
        order.save(update_fields=["status"])
        if order.telegram_user and order.telegram_user.telegram_id:
            notify_order_status(order)

    return redirect(request.META.get("HTTP_REFERER", "/"))


@csrf_exempt
def verify_telegram_auth(request):
    if request.method != "GET":
        return HttpResponseBadRequest("Invalid method")

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return HttpResponseBadRequest("Telegram bot token is not configured")

    next_url = request.GET.get("next")
    allowed_keys = {"id", "username", "first_name", "last_name", "photo_url", "auth_date"}
    data = {key: value for key, value in request.GET.items() if key in allowed_keys or key == "hash"}
    received_hash = data.pop("hash", None)
    if not received_hash:
        return HttpResponseBadRequest("Missing hash")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data.items())
    )

    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return HttpResponseForbidden("Invalid hash")

    auth_date_raw = data.get("auth_date")
    try:
        auth_date = int(auth_date_raw)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid auth_date")

    if TELEGRAM_AUTH_MAX_AGE_SECONDS:
        now = int(time.time())
        if now - auth_date > TELEGRAM_AUTH_MAX_AGE_SECONDS:
            return HttpResponseForbidden("Auth data is too old")

    telegram_id = data.get("id")
    if not telegram_id:
        return HttpResponseBadRequest("Missing telegram id")

    auth_dt = timezone.datetime.fromtimestamp(auth_date, tz=timezone.utc)
    telegram_user, _ = TelegramUser.objects.update_or_create(
        telegram_id=str(telegram_id),
        defaults={
            "username": data.get("username", "") or "",
            "first_name": data.get("first_name", "") or "",
            "last_name": data.get("last_name", "") or "",
            "photo_url": data.get("photo_url", "") or "",
            "auth_date": auth_dt,
        },
    )

    request.session["telegram_user_pk"] = telegram_user.pk
    request.session["telegram_user_id"] = telegram_user.telegram_id
    request.session["telegram_username"] = telegram_user.username

    next_url = next_url or reverse("home")
    return redirect(next_url)


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from shop.models import Product, Order, OrderItem

@csrf_exempt
def api_create_order(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])
        
        if not cart:
            return JsonResponse({'status': 'error', 'error': 'Cart is empty'}, status=400)
        
        # Создаём заказ БЕЗ total_price
        order = Order.objects.create(
            status='new'
        )
        
        # Добавляем товары в заказ
        total = 0
        for item in cart:
            try:
                product = Product.objects.get(id=item['id'])
                quantity = item.get('quantity', 1)
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=quantity
                )
                total += float(product.price) * quantity
            except Product.DoesNotExist:
                pass
        
        return JsonResponse({
            'status': 'ok',
            'order_id': order.id,
            'total': total,
            'message': 'Заказ создан'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

def api_products(request):
    from django.http import JsonResponse
    from django.conf import settings
    from shop.models import Product
    
    products = Product.objects.filter(available=True)
    
    if not products.exists():
        data = [
            {
                "id": 1,
                "title": "Худи",
                "price": 2500.0,
                "image": "products/ChatGPT_Image_10_мар._2026_г._21_27_49.png",
                "description": ""
            },
            {
                "id": 2,
                "title": "Футболка polo Graffiti",
                "price": 1500.0,
                "image": "products/ChatGPT_Image_10_мар._2026_г._21_27_42.png",
                "description": ""
            },
            {
                "id": 3,
                "title": "Лонгслив Street Style",
                "price": 2000.0,
                "image": "products/ChatGPT_Image_9_мар_xWxzpqn._2026_г._18_40_47.png",
                "description": ""
            },
            {
                "id": 4,
                "title": "Майка",
                "price": 1200.0,
                "image": "products/ChatGPT_Image_10_мар._2026_г._21_28_24.png",
                "description": ""
            }
        ]
    else:
        data = []
        for p in products:
            image_name = p.image.name if p.image else ''
            data.append({
                'id': p.id,
                'title': p.title,
                'price': float(p.price),
                'image': image_name,
                'description': p.description or ''
            })
    
    return JsonResponse(data, safe=False)


def debug_version(request):
    import shop.views
    return JsonResponse({
        'file': shop.views.__file__,
        'has_api_create_order': hasattr(shop.views, 'api_create_order')
    })


def debug_function(request):
    import inspect
    from shop.views import api_create_order
    source = inspect.getsource(api_create_order)
    return JsonResponse({
        'source': source[:2000]  # первые 2000 символов
    })
