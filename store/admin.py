from django.contrib import admin
from .models import (
    Category, PartnerBrand, Product, BTSPackage,
    PackageItem, Review, Cart, CartItem, Order, OrderItem,
    Wishlist, WishlistItem, PromoCode
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PartnerBrand)
class PartnerBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price', 'stock', 'is_active', 'is_featured']
    list_filter = ['category', 'brand', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 1


@admin.register(BTSPackage)
class BTSPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'original_price', 'budget_tier', 'is_active', 'is_featured', 'order']
    list_filter = ['budget_tier', 'is_active', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PackageItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'rating', 'title', 'created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'total', 'created_at']
    list_filter = ['status']
    inlines = [OrderItemInline]


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display   = ['code', 'discount_type', 'discount_value', 'max_uses', 'used_count', 'is_active', 'valid_until']
    list_editable  = ['is_active']
    search_fields  = ['code']
    list_filter    = ['discount_type', 'is_active']
    readonly_fields = ['used_count', 'used_by']