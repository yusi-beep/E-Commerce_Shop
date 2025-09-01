from django.shortcuts import render, redirect
from django.db import transaction
from .models import Order, OrderItem
from .forms import CheckoutForm
from cart.cart import Cart


def checkout_view(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    email=form.cleaned_data['email'],
                    full_name=form.cleaned_data['full_name'],
                    address=form.cleaned_data['address'],
                    phone=form.cleaned_data['phone'],
                    total=cart.total()
                )
                for i in cart:
                    OrderItem.objects.create(
                        order=order,
                        product_name=i['name'],
                        unit_price=i['price'],
                        qty=i['qty']
                    )
                cart.clear()
            return redirect('checkout_success')
    else:
        form = CheckoutForm()

    return render(request, 'checkout/checkout.html', {'form': form, 'cart_total': cart.total()})


def checkout_success(request):
    return render(request, 'checkout/success.html')