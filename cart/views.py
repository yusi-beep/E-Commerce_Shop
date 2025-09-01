from django.shortcuts import redirect, render, get_object_or_404
from catalog.models import Product
from .cart import Cart


def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, active=True)
        qty = int(request.POST.get('qty', 1))
        Cart(request).add(product.id, product.name, product.price, qty)
    return redirect('cart_view')


def remove_from_cart(request, product_id):
    Cart(request).remove(product_id)
    return redirect('cart_view')


def cart_view(request):
    cart = Cart(request)
    items = list(cart)
    total = cart.total()
    return render(request, 'cart/cart.html', {'items': items, 'total': total})