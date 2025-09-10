from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import Cart

@require_POST
def add_to_cart(request, product_id):
    qty = int(request.POST.get("qty", 1))
    cart = Cart(request)
    cart.add(product_id=product_id, qty=qty)
    return redirect("cart_detail")

@require_POST
def update_cart(request, product_id):
    qty = int(request.POST.get("qty", 1))
    cart = Cart(request)
    cart.set_qty(product_id=product_id, qty=qty)
    return redirect("cart_detail")

@require_POST
def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id=product_id)
    return redirect("cart_detail")

def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {
        "items": list(cart),
        "total": cart.total(),
    })
