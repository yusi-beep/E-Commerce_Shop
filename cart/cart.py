from decimal import Decimal
from catalog.models import Product
from django.contrib import messages

CART_SESSION_ID = 'cart'


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart  # структура: {str(product_id): {"qty": int}}

    def save(self):
        self.session.modified = True

    def add(self, product_id: int, qty: int = 1):
        """Добавя продукт; не надвишава наличността. Връща реално добавеното количество."""
        product = Product.objects.filter(id=product_id, active=True).first()
        if not product:
            messages.error(self.request, "Продуктът не е намерен.")
            return 0

        qty = max(1, int(qty))
        pid = str(product_id)
        current_qty = int(self.cart.get(pid, {}).get("qty", 0))
        wanted = current_qty + qty

        # лимит до наличността
        allowed = min(wanted, max(0, int(product.stock)))
        diff_added = max(0, allowed - current_qty)

        if diff_added == 0:
            messages.warning(self.request, f"Наличност: {product.stock} бр. Не може да добавиш повече.")
        else:
            self.cart[pid] = {"qty": allowed}
            if allowed < wanted:
                messages.warning(self.request, f"Добавени са {diff_added} бр. (ограничено до наличността: {product.stock}).")
            else:
                messages.success(self.request, f"Добавени {diff_added} бр. от „{product.name}“.")

            self.save()

        return diff_added

    def set_qty(self, product_id: int, qty: int):
        """Задава конкретно количество; валидира спрямо наличността."""
        product = Product.objects.filter(id=product_id, active=True).first()
        if not product:
            messages.error(self.request, "Продуктът не е намерен.")
            return 0

        qty = max(0, int(qty))
        pid = str(product_id)

        if qty == 0:
            if pid in self.cart:
                del self.cart[pid]
                self.save()
                messages.info(self.request, f"Премахнат „{product.name}“ от количката.")
            return 0

        allowed = min(qty, max(0, int(product.stock)))
        self.cart[pid] = {"qty": allowed}
        self.save()

        if allowed < qty:
            messages.warning(self.request, f"Наличност: {product.stock} бр. Количеството е ограничено.")
        else:
            messages.success(self.request, f"Обновено количество: {allowed} бр. за „{product.name}“.")

        return allowed

    def remove(self, product_id: int):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        """Итерация с обогатени данни за продукта (име/цена/тотал)."""
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        for pid, item in self.cart.items():
            p = products.get(int(pid))
            if not p:
                continue
            qty = int(item["qty"])
            price = Decimal(p.price)
            yield {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": price,
                "qty": qty,
                "line_total": price * qty,
            }

    def total(self):
        from decimal import Decimal
        return sum((i["line_total"] for i in self), Decimal("0.00"))

    def is_empty(self):
        return not bool(self.cart)
