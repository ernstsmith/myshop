from django.shortcuts import render, get_object_or_404, redirect
from shop.models import Product, Order, OrderItem

# Главная страница с товарами
def home(request):
    products = Product.objects.filter(available=True)
    return render(request, 'shop/home.html', {'products': products})

# shop/views.py

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


# Просмотр корзины
def cart_view(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        products.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'shop/cart.html', {'products': products, 'total': total})

# Добавление товара в корзину
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

# Удаление товара из корзины
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
    return redirect('cart')

# Оформление заказа
def checkout(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        total = 0
        order = Order.objects.create(
            telegram_user_id=request.POST.get('telegram_user_id', ''),
            total_amount=0,
            paid=False
        )
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            subtotal = product.price * quantity
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)
            total += subtotal
        order.total_amount = total
        order.save()
        request.session['cart'] = {}  # очищаем корзину
        return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        products = []
        total = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            subtotal = product.price * quantity
            products.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
            total += subtotal
        return render(request, 'shop/checkout.html', {'products': products, 'total': total})

def products_page(request):
    products = Product.objects.all()
    return render(request, 'shop/products_page.html', {'products': products})

def gallery(request):
    return render(request, 'shop/gallery.html')
