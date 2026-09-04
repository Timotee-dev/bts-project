from django import forms
from .models import Vendor
from store.models import Product, BTSPackage, PackageItem, Category


class VendorRegistrationForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['business_name', 'description', 'phone', 'email', 'logo',
                  'bank_name', 'account_number', 'account_name',
                  'instagram', 'twitter', 'website']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'image',
                  'image2', 'image3', 'available_colors', 'available_sizes', 'stock', 'is_active', 'is_featured']
        widgets = {
            'description':    forms.Textarea(attrs={'rows': 4}),
            'available_colors': forms.TextInput(attrs={'placeholder': 'e.g. Black, White, Navy Blue, Red'}),
            'available_sizes':  forms.TextInput(attrs={'placeholder': 'e.g. S,M,L,XL or 36,37,38,39'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


class VendorPackageForm(forms.ModelForm):
    class Meta:
        model = BTSPackage
        fields = ['name', 'description', 'cover_image', 'price',
                  'original_price', 'budget_tier', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }