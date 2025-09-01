from decimal import Decimal

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if cart is None:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product_id, name, price, qty=1):
        pid = str(product_id)
        item = self.cart.get(pid, {"name": name, "qty": 0, "price": str(price)})
        item["qty"] += int(qty)
        self.cart[pid] = item
        self.session.modified = True

    def remove(self, product_id):
        self.cart.pop(str(product_id), None)
        self.session.modified = True

    def clear(self):
        self.session['cart'] = {}
        self.session.modified = True

    def __iter__(self):
        for pid, item in self.cart.items():
            price = Decimal(item['price'])
            yield {
                'id': pid,
                'name': item['name'],
                'qty': item['qty'],
                'price': price,
                'subtotal': price * item['qty'],
            }

    def total(self):
        return sum(Decimal(i['price']) * i['qty'] for i in self.cart.values())