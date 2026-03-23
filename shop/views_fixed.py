import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from shop.models import Product, Order, OrderItem, TelegramUser
from django.conf import settings

@csrf_exempt
def api_create_order(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])
        
        if not cart:
            return JsonResponse({'status': 'error', 'error': 'Cart is empty'}, status=400)
        
        # Создаём заказ
        order = Order.objects.create(status='new')
        
        # Добавляем товары
        total = 0
        for item in cart:
            product = Product.objects.get(id=item['id'])
            quantity = item.get('quantity', 1)
            price = float(product.price)
            
            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=quantity
            )
            total += price * quantity
        
        order.total_price = total
        order.save()
        
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
