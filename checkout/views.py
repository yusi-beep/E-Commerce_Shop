from decimal import Decimal
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Order, OrderItem, Coupon
from .forms import CheckoutForm
from cart.cart import Cart
from catalog.models import Product

# Stripe е опционален
try:
    import stripe
except Exception:
    stripe = None

if getattr(settings, 'USE_STRIPE', False) and stripe and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    # деактивирай Stripe ако няма ключове/флаг
    setattr(settings, 'USE_STRIPE', False)


def checkout_view(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart_total = cart.total()

            # Промокод
            code = form.cleaned_data.get('coupon', '').strip()
            applied_coupon = None
            if code:
                try:
                    c = Coupon.objects.get(code__iexact=code)
                    if c.is_valid():
                        cart_total = c.apply(cart_total)
                        applied_coupon = c
                except Coupon.DoesNotExist:
                    applied_coupon = None

            payment_method = form.cleaned_data.get('payment_method', 'cod')

            # Създаване на поръчката и редовете
            with transaction.atomic():
                order = Order.objects.create(
                    email=form.cleaned_data['email'],
                    full_name=form.cleaned_data['full_name'],
                    address=form.cleaned_data['address'],
                    phone=form.cleaned_data['phone'],
                    total=cart_total,
                    status=Order.Status.NEW,
                )
                line_items = []
                for i in cart:
                    product_obj = Product.objects.filter(id=i['id']).first()
                    OrderItem.objects.create(
                        order=order,
                        product=product_obj,
                        product_name=i['name'],
                        unit_price=i['price'],
                        qty=i['qty'],
                    )
                    line_items.append({
                        'name': i['name'],
                        'amount': int(Decimal(i['price']) * 100),
                        'qty': int(i['qty']),
                    })


            # Ако е наложен платеж → без Stripe
            if payment_method == 'cod' or not settings.USE_STRIPE:
                # намаляване на наличности
                for it in order.items.select_related('product'):
                    if it.product:
                        it.product.stock = max(0, int(it.product.stock) - int(it.qty))
                        it.product.save(update_fields=['stock'])

                # (по желание) изпрати имейл „получена поръчка“
                try:
                    subject = f"Получена поръчка №{order.id}"
                    message = (
                        f"Здравейте, {order.full_name}!\n\n"
                        f"Получихме вашата поръчка №{order.id}. Плащане: Наложен платеж.\n"
                        f"Сума: {order.total} лв\n"
                        "Ще се свържем при нужда.\n"
                    )
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
                except Exception:
                    pass

                # Изчисти количката и прати към success
                cart.clear()
                return redirect('checkout_success')

            # Иначе – Stripe Checkout (само ако USE_STRIPE == True)
            # Заб: тук НЯМА да стигнем ако няма ключове.
            import stripe as _stripe  # локален alias за сигурност
            success_url = f"{settings.SITE_URL}/checkout/success/"
            cancel_url = f"{settings.SITE_URL}/checkout/cancel/"

            # Преобразуване на line_items към Stripe формат
            stripe_line_items = [{
                'price_data': {
                    'currency': 'bgn',
                    'product_data': {'name': it['name']},
                    'unit_amount': it['amount'],
                },
                'quantity': it['qty'],
            } for it in line_items]

            metadata = {'order_id': str(order.id)}
            if applied_coupon:
                metadata['coupon_code'] = applied_coupon.code

            session = _stripe.checkout.Session.create(
                mode='payment',
                line_items=stripe_line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                customer_email=order.email,
            )
            return redirect(session.url)
    else:
        form = CheckoutForm()

    return render(request, 'checkout/checkout.html', {
        'form': form,
        'cart_total': cart.total(),
        'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY if getattr(settings, 'USE_STRIPE', False) else '',
    })


def checkout_success(request):
    # Ако плащането е било COD, количката вече е изчистена в checkout_view.
    # Ако Stripe – изчистването може да е тук или в webhook по избор.
    return render(request, 'checkout/success.html')


def checkout_cancel(request):
    return render(request, 'checkout/cancel.html')


@csrf_exempt
def stripe_webhook(request):
    # Ако Stripe е изключен – просто приеми 200
    if not getattr(settings, 'USE_STRIPE', False):
        return HttpResponse(status=200)

    import stripe as _stripe
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = _stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        data = event['data']['object']
        order_id = data.get('metadata', {}).get('order_id')
        coupon_code = data.get('metadata', {}).get('coupon_code')

        if order_id:
            for it in order.items.select_related('product'):
                if it.product:
                    it.product.stock = max(0, int(it.product.stock) - int(it.qty))
                    it.product.save(update_fields=['stock'])
            try:
                order = Order.objects.get(id=order_id)
                order.set_status(Order.Status.PAID)
                if coupon_code:
                    try:
                        c = Coupon.objects.get(code__iexact=coupon_code)
                        c.used = (c.used or 0) + 1
                        c.save(update_fields=['used'])
                    except Coupon.DoesNotExist:
                        pass
                # Имейл за платена поръчка
                subject = render_to_string('email/order_paid_subject.txt', {'order': order}).strip()
                message = render_to_string('email/order_paid.txt', {'order': order})
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
            except Order.DoesNotExist:
                pass

    return HttpResponse(status=200)
