from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('telegram/auth/', views.verify_telegram_auth, name='telegram_auth'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # <-- добавлено
    path('products/', views.products_page, name='products_page'),
    path('gallery/', views.gallery, name='gallery'),
    path('vk/', views.vk_miniapp, name='vk_miniapp'),
    path("miniapp/", views.miniapp, name="miniapp"),
    path("api/order/", views.api_create_order, name="api_create_order"),
    path("api/products/", views.api_products, name="api_products"),
]
