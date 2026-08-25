from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer, Address


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('BTS Profile', {'fields': ('phone', 'university', 'state', 'profile_picture')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'full_name', 'city', 'state', 'is_default']