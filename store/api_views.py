from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Category, Product, BTSPackage, PartnerBrand, Cart, CartItem, Order
from .serializers import (
    CategorySerializer, ProductSerializer, BTSPackageSerializer,
    PartnerBrandSerializer, CartSerializer, OrderSerializer
)


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(customer=request.user, defaults={'session_key': ''})
    else:
        key = request.session.session_key or ''
        if not key:
            request.session.create()
            key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=key, customer=None)
    return cart


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('q')
        featured = self.request.query_params.get('featured')
        if category:
            qs = qs.filter(category__slug=category)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if featured:
            qs = qs.filter(is_featured=True)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = 'slug'


class PackageListView(generics.ListAPIView):
    serializer_class = BTSPackageSerializer

    def get_queryset(self):
        qs = BTSPackage.objects.filter(is_active=True)
        tier = self.request.query_params.get('tier')
        if tier:
            qs = qs.filter(budget_tier=tier)
        return qs


class PackageDetailView(generics.RetrieveAPIView):
    queryset = BTSPackage.objects.filter(is_active=True)
    serializer_class = BTSPackageSerializer
    lookup_field = 'slug'


class BrandListView(generics.ListAPIView):
    queryset = PartnerBrand.objects.all()
    serializer_class = PartnerBrandSerializer


class BrandDetailView(generics.RetrieveAPIView):
    queryset = PartnerBrand.objects.all()
    serializer_class = PartnerBrandSerializer
    lookup_field = 'slug'


class CartView(APIView):
    def get(self, request):
        cart = get_or_create_cart(request)
        return Response(CartSerializer(cart).data)


class AddToCartView(APIView):
    def post(self, request):
        cart = get_or_create_cart(request)
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        size = request.data.get('size', '')

        if item_type == 'package':
            pkg = get_object_or_404(BTSPackage, id=item_id)
            CartItem.objects.get_or_create(cart=cart, package=pkg, defaults={'quantity': 1})
            cart.cart_type = 'package'
            cart.save()
        elif item_type == 'product':
            product = get_object_or_404(Product, id=item_id)
            item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, selected_size=size, defaults={'quantity': 1}
            )
            if not created:
                item.quantity += 1
                item.save()
            cart.cart_type = 'custom'
            cart.save()
        else:
            return Response({'error': 'Invalid item type'}, status=400)

        return Response(CartSerializer(cart).data)


class RemoveFromCartView(APIView):
    def delete(self, request, item_id):
        cart = get_or_create_cart(request)
        CartItem.objects.filter(id=item_id, cart=cart).delete()
        return Response(CartSerializer(cart).data)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)
