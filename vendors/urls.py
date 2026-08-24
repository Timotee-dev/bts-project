from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.vendor_register, name='vendor_register'),
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('products/', views.vendor_products, name='vendor_products'),
    path('products/add/', views.vendor_product_add, name='vendor_product_add'),
    path('products/<int:pk>/edit/', views.vendor_product_edit, name='vendor_product_edit'),
    path('products/<int:pk>/delete/', views.vendor_product_delete, name='vendor_product_delete'),
    path('packages/', views.vendor_packages, name='vendor_packages'),
    path('packages/add/', views.vendor_package_add, name='vendor_package_add'),
    path('packages/<int:pk>/edit/', views.vendor_package_edit, name='vendor_package_edit'),
    path('orders/', views.vendor_orders, name='vendor_orders'),
    path('orders/<str:order_number>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('settings/', views.vendor_settings, name='vendor_settings'),
    path('store/<slug:slug>/', views.vendor_storefront, name='vendor_storefront'),
]
