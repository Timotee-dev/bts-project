from django.contrib import admin
from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'is_verified', 'joined_at']
    list_filter = ['status', 'is_verified']
    search_fields = ['business_name', 'user__email']
    actions = ['activate', 'suspend']

    def activate(self, request, queryset):
        queryset.update(status='active')
    activate.short_description = 'Activate selected vendors'

    def suspend(self, request, queryset):
        queryset.update(status='suspended')
    suspend.short_description = 'Suspend selected vendors'
