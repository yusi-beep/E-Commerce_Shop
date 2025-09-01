from django.db import models

class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    full_name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    paid = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()

    def line_total(self):
        return self.unit_price * self.qty