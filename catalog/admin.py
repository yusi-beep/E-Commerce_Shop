from django.contrib import admin
from .models import Category, Product, ProductImage
from django.forms.models import BaseInlineFormSet

class MaxFiveInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Броим валидните форми (без изтритите)
        total = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('image'):
                    total += 1
        # Плюс вече съществуващите в БД (ако е промяна)
        instance = getattr(self, 'instance', None)
        existing = 0
        if instance and instance.pk:
            existing = instance.images.count()
            # При промяна: total е само новите/редактирани; реалният лимит е (existing + нови - изтрити)
            # По-просто: ще оставим моделът да валидира при save; тук само soft-лимит:
        if total > 5:
            from django.core.exceptions import ValidationError
            raise ValidationError("Може да качите най-много 5 допълнителни снимки.")

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    max_num = 5
    formset = MaxFiveInlineFormSet
    fields = ('image', 'image_webp', 'image_avif', 'alt_text', 'sort_order')
    readonly_fields = ('image_webp', 'image_avif')
    ordering = ('sort_order',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'active')
    list_filter = ('active', 'category')
    search_fields = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    readonly_fields = ('image_webp', 'image_avif')
    fields = (
        'name', 'slug', 'category', 'description', 'price', 'old_price', 'stock', 'active',
        'image', 'image_webp', 'image_avif',   # <- добавени тук за визуализация
        # добави и други полета, които имаш
    )
