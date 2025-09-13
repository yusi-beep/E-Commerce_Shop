from django.db import models
from django.utils import timezone
from catalog.models import Product, ProductVariant

class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'Нова'
        PAID = 'PAID', 'Платена'
        FULFILLED = 'FULFILLED', 'Изпълнена'
        CANCELED = 'CANCELED', 'Отменена'
        REFUNDED = 'REFUNDED', 'Възстановена'

    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    full_name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    paid = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name} ({self.get_status_display()})"

    def set_status(self, new_status: str, save=True):
        self.status = new_status
        if new_status == self.Status.PAID:
            self.paid = True
        if save:
            self.save(update_fields=['status', 'paid'])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()

    def line_total(self):
        return self.unit_price * self.qty

    def __str__(self):
        return f"{self.product_name} x{self.qty}"

class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    percent_off = models.PositiveIntegerField(null=True, blank=True)  # 0-100
    amount_off = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # BGN
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def apply(self, total):
        from decimal import Decimal
        res = Decimal(total)
        if self.percent_off:
            res = res * (Decimal('100') - Decimal(self.percent_off)) / Decimal('100')
        if self.amount_off:
            res = max(Decimal('0'), res - self.amount_off)
        return res

    def is_valid(self):
        if not self.active:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses and self.used >= self.max_uses:
            return False
        return True
