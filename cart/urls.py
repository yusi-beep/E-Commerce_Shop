from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:product_id>/", views.add_to_cart, name="cart_add"),
    path("update/<int:product_id>/", views.update_cart, name="cart_update"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="cart_remove"),
]
