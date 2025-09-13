from .models import SiteBranding
from cart.cart import Cart


def branding_context(request):
    """
    Context processor to make branding and cart info available 
    in all templates.
    """
    branding = SiteBranding.get_current()
    cart = Cart(request)
    
    # Count total number of items in cart (not unique products, but total quantity)
    cart_item_count = sum(item.get('qty', 0) for item in cart.cart.values())
    
    context = {
        'site_branding': branding,
        'cart_item_count': cart_item_count,
    }
    
    return context