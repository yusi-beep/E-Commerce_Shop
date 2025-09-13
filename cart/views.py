from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from catalog.models import Product, ProductVariant
from .cart import Cart

@require_POST
def add_to_cart(request, product_id):
    qty = int(request.POST.get("qty", 1))
    variant_id = request.POST.get("variant_id")
    cart = Cart(request)
    
    if variant_id:
        # Add variant to cart
        cart.add_variant(variant_id=int(variant_id), qty=qty)
    else:
        # Add product without variant
        cart.add(product_id=product_id, qty=qty)
    
    return redirect("cart_detail")

@require_POST
def update_cart(request, cart_item_id):
    qty = int(request.POST.get("qty", 1))
    cart = Cart(request)
    cart.set_qty(cart_item_id=cart_item_id, qty=qty)
    return redirect("cart_detail")

@require_POST
def remove_from_cart(request, cart_item_id):
    cart = Cart(request)
    cart.remove(cart_item_id=cart_item_id)
    return redirect("cart_detail")

def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {
        "items": list(cart),
        "total": cart.total(),
    })
