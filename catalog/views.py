from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def product_list(request):
    category_slug = request.GET.get('c')
    products = Product.objects.filter(active=True)
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=current_category)
    categories = Category.objects.all()
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': current_category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'catalog/product_detail.html', {'product': product})