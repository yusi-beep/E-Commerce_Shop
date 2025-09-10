from django.db import models
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from io import BytesIO
from PIL import Image
import os

BGN_PER_EUR = Decimal('1.95583')

# опитай да заредиш AVIF плъгина; ако го няма, просто няма да правим avif
try:
    import pillow_avif  # noqa: F401
    HAS_AVIF = True
except Exception:
    HAS_AVIF = False

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

    # нови полета (деривати)
    image_webp = models.ImageField(upload_to='products/', blank=True, null=True, editable=False)
    image_avif = models.ImageField(upload_to='products/', blank=True, null=True, editable=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    # --- helper-и за деривати ---
    def _save_derivative(self, source_field_name: str, fmt: str, target_field_name: str, quality: int = 85):
        src_field = getattr(self, source_field_name)
        if not src_field:
            return
        src_field.open()
        im = Image.open(src_field)
        im.load()

        out = BytesIO()
        base, _ext = os.path.splitext(os.path.basename(src_field.name))
        fname = f"products/main/{slugify(base)}.{fmt}"

        opts = {}
        if fmt == "webp":
            opts = {"quality": quality, "method": 6}  # method 6 = по-добра компресия
        elif fmt == "avif":
            opts = {"quality": quality}               # 0-100

        im.save(out, format=fmt.upper(), **opts)
        out.seek(0)

        # сетни във временния FileField на модела (без save на целия модел)
        target_field = getattr(self, target_field_name)
        target_field.save(fname, out, save=False)

    def save(self, *args, **kwargs):
        # първо запази, за да имаме път към оригинала
        super().save(*args, **kwargs)

        # ако има главна снимка, генерирай деривати
        if self.image:
            try:
                self._save_derivative("image", "webp", "image_webp", quality=85)
            except Exception:
                pass
            if HAS_AVIF:
                try:
                    self._save_derivative("image", "avif", "image_avif", quality=50)
                except Exception:
                    pass

            # запази само дериватните полета
            super().save(update_fields=["image_webp", "image_avif"])

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

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/extra/')
    # нови полета за деривати:
    image_webp = models.ImageField(upload_to='products/extra/', blank=True, null=True, editable=False)
    image_avif = models.ImageField(upload_to='products/extra/', blank=True, null=True, editable=False)
    alt_text = models.CharField(max_length=120, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"

    def clean(self):
        # Ограничение: максимум 5 допълнителни снимки за продукт
        if self.product_id and self._state.adding:
            count = ProductImage.objects.filter(product_id=self.product_id).count()
            if count >= 5:
                raise ValidationError("Може да качите най-много 5 допълнителни снимки за продукт.")

    # ---- helper-и за конвертиране ----
    def _save_derivative(self, fmt: str, quality: int = 85):
        """Създай webp/avif вариант и го запиши в съответното поле."""
        if not self.image:
            return

        # отваряме оригинала
        self.image.open()
        im = Image.open(self.image)
        im.load()

        # правим без загуба на EXIF ориентация (по желание може да нормализираш)
        out = BytesIO()

        base, _ext = os.path.splitext(os.path.basename(self.image.name))
        fname = f"products/extra/{slugify(base)}.{fmt}"

        opts = {}
        if fmt == "webp":
            # lossless можеш да пуснеш с: opts = {"lossless": True}
            opts = {"quality": quality, "method": 6}
        elif fmt == "avif":
            # pillow-avif-plugin: quality 0-100
            opts = {"quality": quality}

        im.save(out, format=fmt.upper(), **opts)
        out.seek(0)

        django_file = models.FileField().to_python(fname)
        # избираме правилното поле
        if fmt == "webp":
            self.image_webp.save(fname, out, save=False)
        elif fmt == "avif":
            self.image_avif.save(fname, out, save=False)
    def save(self, *args, **kwargs):
        """При запис — създаваме/обновяваме webp (+ avif ако има плъгин)."""
        super().save(*args, **kwargs)  # първо запиши оригинала (за да има self.image.path/url)

        # Генерирай WEBP винаги
        try:
            self._save_derivative("webp", quality=85)
        except Exception:
            pass

        # Генерирай AVIF, ако имаме плъгин
        if HAS_AVIF:
            try:
                self._save_derivative("avif", quality=50)  # avif често дава отличен размер и на по-ниско качество
            except Exception:
                pass

        # запази отново, за да запишем и дериватите
        super().save(update_fields=['image_webp', 'image_avif'])
        
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