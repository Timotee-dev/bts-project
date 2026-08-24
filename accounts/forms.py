from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Customer


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=20, required=False)
    university = forms.CharField(max_length=200, required=False)

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'university', 'password1', 'password2']


class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'university', 'state', 'profile_picture']
