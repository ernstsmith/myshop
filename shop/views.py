from django.shortcuts import render
from .models import Product

def home(request):
    products = Product.objects.filter(available=True)
    return render(request, 'shop/home.html', {'products': products})
