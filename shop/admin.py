from django.contrib import admin
from .models import Product, Cart, CartItem, Order, OrderItem, TelegramUser


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'available')
    prepopulated_fields = {'slug': ('title',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tg_username',
        'tg_user_id',
        'total_amount',
        'status',
        'created_at'
    )

    list_filter = ('status', 'paid', 'created_at')

    inlines = [OrderItemInline]


admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(TelegramUser)
