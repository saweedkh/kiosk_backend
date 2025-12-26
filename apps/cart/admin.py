from django.contrib import admin
from apps.cart.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'created_at']
    list_filter = ['created_at']
    search_fields = ['session_key']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name']
    readonly_fields = ['subtotal', 'created_at', 'updated_at']
