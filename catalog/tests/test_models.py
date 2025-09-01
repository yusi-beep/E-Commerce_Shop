import pytest
from decimal import Decimal
from catalog.models import Category, Product

@pytest.mark.django_db
def test_price_eur():
    c = Category.objects.create(name='X', slug='x')
    p = Product.objects.create(category=c, name='A', slug='a', price=Decimal('19.56'))
    assert p.price_eur is not None