from django.urls import path
from . import api_views

urlpatterns = [
    path('categories/', api_views.CategoryListView.as_view(), name='api-categories'),
    path('products/', api_views.ProductListView.as_view(), name='api-products'),
    path('products/<slug:slug>/', api_views.ProductDetailView.as_view(), name='api-product-detail'),
    path('packages/', api_views.PackageListView.as_view(), name='api-packages'),
    path('packages/<slug:slug>/', api_views.PackageDetailView.as_view(), name='api-package-detail'),
    path('brands/', api_views.BrandListView.as_view(), name='api-brands'),
    path('brands/<slug:slug>/', api_views.BrandDetailView.as_view(), name='api-brand-detail'),
    path('cart/', api_views.CartView.as_view(), name='api-cart'),
    path('cart/add/', api_views.AddToCartView.as_view(), name='api-cart-add'),
    path('cart/remove/<int:item_id>/', api_views.RemoveFromCartView.as_view(), name='api-cart-remove'),
    path('orders/', api_views.OrderListView.as_view(), name='api-orders'),
    path('orders/<str:order_number>/', api_views.OrderDetailView.as_view(), name='api-order-detail'),
]
