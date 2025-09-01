from django import forms

class CheckoutForm(forms.Form):
    email = forms.EmailField(label='Имейл')
    full_name = forms.CharField(label='Име и фамилия', max_length=120)
    address = forms.CharField(label='Адрес', max_length=255)
    phone = forms.CharField(label='Телефон', max_length=32, required=False)
    coupon = forms.CharField(label='Промокод', max_length=40, required=False)