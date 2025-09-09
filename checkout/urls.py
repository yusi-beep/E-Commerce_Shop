from django.urls import path
from . import views

urlpatterns = [
    path('', views.checkout_view, name='checkout_view'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]