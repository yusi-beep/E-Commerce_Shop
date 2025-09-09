from django.db import models
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP

BGN_PER_EUR = Decimal('1.95583')

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    # Цени в лева (основна валута)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    # Автоматично изчисляване в евро (само за показване)
    @property
    def price_eur(self):
        if self.price is None:
            return None
        return (Decimal(self.price) / BGN_PER_EUR).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def old_price_eur(self):
        if self.old_price is None:
            return None
        return (Decimal(self.old_price) / BGN_PER_EUR).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def discount_percent(self):
        """Цяло число за -XX% ако има old_price > price, иначе None."""
        if self.old_price and self.old_price > self.price and self.old_price > 0:
            pct = (Decimal(self.old_price) - Decimal(self.price)) / Decimal(self.old_price) * Decimal('100')
            return pct.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return None
        
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=64, unique=True)
    size = models.CharField(max_length=32, blank=True)
    color = models.CharField(max_length=32, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        attrs = ", ".join(a for a in [self.size, self.color] if a)
        return f"{self.product.name} [{attrs or self.sku}]"