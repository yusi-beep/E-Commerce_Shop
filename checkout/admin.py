from django.contrib import admin
from .models import Order, OrderItem, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "total", "paid", "status", "created_at")
    list_filter = ("paid", "status", "created_at")
    search_fields = ("full_name", "email")
    inlines = [OrderItemInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "percent_off", "amount_off", "active", "valid_from", "valid_to", "used")
    list_filter = ("active",)
    search_fields = ("code",)