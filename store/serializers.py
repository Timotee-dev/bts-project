from rest_framework import serializers
from .models import (
    Category, PartnerBrand, Product, BTSPackage, PackageItem,
    Review, Cart, CartItem, Order, OrderItem, Wishlist, WishlistItem
)


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'image', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class PartnerBrandSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = PartnerBrand
        fields = ['id', 'name', 'slug', 'logo', 'description', 'categories',
                  'instagram', 'twitter', 'website', 'product_count', 'is_featured']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.SerializerMethodField()
    sizes_list = serializers.ListField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'brand',
                  'brand_name', 'description', 'price', 'image', 'image2', 'image3',
                  'sizes_list', 'stock', 'is_active', 'is_featured', 'average_rating',
                  'review_count', 'created_at']

    def get_review_count(self, obj):
        return obj.reviews.count()


class PackageItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = PackageItem
        fields = ['id', 'product', 'quantity']


class BTSPackageSerializer(serializers.ModelSerializer):
    package_items = PackageItemSerializer(many=True, read_only=True)
    savings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings_percent = serializers.IntegerField(read_only=True)
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = BTSPackage
        fields = ['id', 'name', 'slug', 'description', 'cover_image', 'price',
                  'original_price', 'savings', 'savings_percent', 'budget_tier',
                  'package_items', 'is_active', 'is_featured', 'review_count']

    def get_review_count(self, obj):
        return obj.reviews.count()


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'customer_name', 'rating', 'title', 'body', 'created_at']
        read_only_fields = ['customer_name', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    package = BTSPackageSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'package', 'quantity', 'selected_size', 'line_total']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    packaging_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_checkout = serializers.BooleanField(read_only=True)
    custom_item_count = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'cart_type', 'items', 'subtotal', 'packaging_fee',
                  'total', 'can_checkout', 'custom_item_count', 'total_items']


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'unit_price', 'selected_size', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'subtotal', 'packaging_fee',
                  'total', 'shipping_address', 'notes', 'items', 'created_at', 'updated_at']
