from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category


def product_list(request):
    # приемай и ?cat=... и ?c=...
    cat_slug = request.GET.get('cat') or request.GET.get('c')
    sort = request.GET.get('sort', 'name')  # name | -name | price | -price | stock | -stock

    # базов queryset + оптимизация
    qs = (
        Product.objects.filter(active=True)
        .select_related('category')
        .prefetch_related('images')
    )

    current_category = None
    if cat_slug:
        current_category = get_object_or_404(Category, slug=cat_slug)
        qs = qs.filter(category=current_category)

    # безопасно сортиране
    allowed_sorts = {'name', '-name', 'price', '-price', 'stock', '-stock'}
    if sort not in allowed_sorts:
        sort = 'name'
    qs = qs.order_by(sort)

    # категории за сайдбара
    categories = Category.objects.all().order_by('name')

    # (по избор) странициране – 20 на страница
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'catalog/product_list.html',
        {
            'products': page_obj.object_list,
            'page_obj': page_obj,
            'categories': categories,
            'current_category': current_category,
            'current_sort': sort,
            'current_cat_slug': cat_slug,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug,
        active=True,
    )
    return render(request, 'catalog/product_detail.html', {'product': product})
