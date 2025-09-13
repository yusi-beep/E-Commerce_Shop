from decimal import Decimal
from catalog.models import Product, ProductVariant
from django.contrib import messages

CART_SESSION_ID = 'cart'


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart  # структура: {cart_item_id: {"type": "variant"/"product", "item_id": int, "qty": int}}

    def save(self):
        self.session.modified = True

    def add_variant(self, variant_id: int, qty: int = 1):
        """Добавя вариант на продукт; не надвишава наличността. Връща реално добавеното количество."""
        variant = ProductVariant.objects.select_related('product').filter(id=variant_id, product__active=True).first()
        if not variant:
            messages.error(self.request, "Вариантът не е намерен.")
            return 0

        qty = max(1, int(qty))
        cart_item_id = f"v{variant_id}"
        current_qty = int(self.cart.get(cart_item_id, {}).get("qty", 0))
        wanted = current_qty + qty

        # лимит до наличността на варианта
        allowed = min(wanted, max(0, int(variant.stock)))
        diff_added = max(0, allowed - current_qty)

        variant_display = f"{variant.product.name}"
        if variant.size or variant.color:
            attrs = ", ".join(a for a in [variant.size, variant.color] if a)
            variant_display += f" [{attrs}]"

        if diff_added == 0:
            messages.warning(self.request, f"Наличност: {variant.stock} бр. Не може да добавиш повече за {variant_display}.")
        else:
            self.cart[cart_item_id] = {
                "type": "variant",
                "item_id": variant_id,
                "qty": allowed
            }
            if allowed < wanted:
                messages.warning(self.request, f"Добавени са {diff_added} бр. (ограничено до наличността: {variant.stock}) за {variant_display}.")
            else:
                messages.success(self.request, f"Добавени {diff_added} бр. от {variant_display}.")

            self.save()

        return diff_added

    def add(self, product_id: int, qty: int = 1):
        """Добавя продукт без вариант; не надвишава наличността. Връща реално добавеното количество."""
        product = Product.objects.filter(id=product_id, active=True).first()
        if not product:
            messages.error(self.request, "Продуктът не е намерен.")
            return 0

        qty = max(1, int(qty))
        cart_item_id = f"p{product_id}"
        current_qty = int(self.cart.get(cart_item_id, {}).get("qty", 0))
        wanted = current_qty + qty

        # лимит до наличността
        allowed = min(wanted, max(0, int(product.stock)))
        diff_added = max(0, allowed - current_qty)

        if diff_added == 0:
            messages.warning(self.request, f"Наличност: {product.stock} бр. Не може да добавиш повече.")
        else:
            self.cart[cart_item_id] = {
                "type": "product",
                "item_id": product_id,
                "qty": allowed
            }
            if allowed < wanted:
                messages.warning(self.request, f"Добавени са {diff_added} бр. (ограничено до наличността: {product.stock}).")
            else:
                messages.success(self.request, f"Добавени {diff_added} бр. от '{product.name}'.")

            self.save()

        return diff_added

    def set_qty(self, cart_item_id: str, qty: int):
        """Задава конкретно количество за cart item; валидира спрямо наличността."""
        if cart_item_id not in self.cart:
            messages.error(self.request, "Продуктът не е намерен в количката.")
            return 0

        item = self.cart[cart_item_id]
        qty = max(0, int(qty))

        if qty == 0:
            del self.cart[cart_item_id]
            self.save()
            messages.info(self.request, "Продуктът е премахнат от количката.")
            return 0

        # Get the item for stock validation
        if item["type"] == "variant":
            variant = ProductVariant.objects.select_related('product').filter(id=item["item_id"], product__active=True).first()
            if not variant:
                messages.error(self.request, "Вариантът не е намерен.")
                return 0
            
            allowed = min(qty, max(0, int(variant.stock)))
            
            variant_display = f"{variant.product.name}"
            if variant.size or variant.color:
                attrs = ", ".join(a for a in [variant.size, variant.color] if a)
                variant_display += f" [{attrs}]"
            
            display_name = variant_display
            stock = variant.stock
        else:  # product
            product = Product.objects.filter(id=item["item_id"], active=True).first()
            if not product:
                messages.error(self.request, "Продуктът не е намерен.")
                return 0
            
            allowed = min(qty, max(0, int(product.stock)))
            display_name = product.name
            stock = product.stock

        self.cart[cart_item_id]["qty"] = allowed
        self.save()

        if allowed < qty:
            messages.warning(self.request, f"Наличност: {stock} бр. Количеството е ограничено.")
        else:
            messages.success(self.request, f"Обновено количество: {allowed} бр. за '{display_name}'.")

        return allowed

    def remove(self, cart_item_id: str):
        if cart_item_id in self.cart:
            del self.cart[cart_item_id]
            self.save()

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        """Итерация с обогатени данни за продукта/варианта (име/цена/тотал)."""
        variant_ids = []
        product_ids = []
        
        # Collect all IDs
        for cart_item_id, item in self.cart.items():
            if item["type"] == "variant":
                variant_ids.append(item["item_id"])
            elif item["type"] == "product":
                product_ids.append(item["item_id"])

        # Fetch variants and products
        variants = {v.id: v for v in ProductVariant.objects.select_related('product').filter(id__in=variant_ids)}
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        
        for cart_item_id, item in self.cart.items():
            qty = int(item["qty"])
            
            if item["type"] == "variant":
                variant = variants.get(item["item_id"])
                if not variant:
                    continue
                
                price = Decimal(variant.price)
                name = variant.product.name
                if variant.size or variant.color:
                    attrs = ", ".join(a for a in [variant.size, variant.color] if a)
                    name += f" [{attrs}]"
                
                yield {
                    "cart_item_id": cart_item_id,
                    "type": "variant",
                    "id": variant.product.id,  # Product ID for template compatibility
                    "variant_id": variant.id,
                    "name": name,
                    "slug": variant.product.slug,
                    "size": variant.size,
                    "color": variant.color,
                    "sku": variant.sku,
                    "price": price,
                    "qty": qty,
                    "line_total": price * qty,
                }
            
            elif item["type"] == "product":
                product = products.get(item["item_id"])
                if not product:
                    continue
                
                price = Decimal(product.price)
                yield {
                    "cart_item_id": cart_item_id,
                    "type": "product",
                    "id": product.id,
                    "variant_id": None,
                    "name": product.name,
                    "slug": product.slug,
                    "size": "",
                    "color": "",
                    "sku": "",
                    "price": price,
                    "qty": qty,
                    "line_total": price * qty,
                }

    def total(self):
        from decimal import Decimal
        return sum((i["line_total"] for i in self), Decimal("0.00"))

    def is_empty(self):
        return not bool(self.cart)