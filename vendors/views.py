from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from store.models import Product, BTSPackage, PackageItem, Order, OrderItem
from .models import Vendor
from .forms import VendorRegistrationForm, VendorProductForm, VendorPackageForm


def vendor_register(request):
    # If already a vendor, go to dashboard
    try:
        if request.user.is_authenticated and request.user.vendor:
            return redirect('vendor_dashboard')
    except Exception:
        pass

    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/vendors/register/')

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.save()
            messages.success(request, f'🎉 Welcome! Your store "{vendor.business_name}" is live.')
            return redirect('vendor_dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = VendorRegistrationForm(initial={
            'email': request.user.email,
            'phone': getattr(request.user, 'phone', ''),
        })
    return render(request, 'vendors/register.html', {'form': form})


def _get_vendor(request):
    """Helper — get vendor for logged in user or redirect."""
    try:
        return request.user.vendor
    except Exception:
        messages.error(request, 'You don\'t have a vendor account yet.')
        return None


@login_required
def vendor_dashboard(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')

    recent_orders = Order.objects.filter(
        items__product__vendor=vendor
    ).distinct().order_by('-created_at')[:8]

    from django.utils import timezone
    now = timezone.now()
    monthly_items = OrderItem.objects.filter(
        product__vendor=vendor,
        order__paid_at__year=now.year,
        order__paid_at__month=now.month,
        order__payment_status='paid',
    )
    monthly_revenue = sum(i.line_total for i in monthly_items)
    total_revenue = sum(i.line_total for i in OrderItem.objects.filter(
        product__vendor=vendor,
        order__payment_status='paid',
    ))

    return render(request, 'vendors/dashboard.html', {
        'vendor': vendor,
        'recent_orders': recent_orders,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
    })


@login_required
def vendor_products(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    products = vendor.products.all().order_by('-created_at')
    return render(request, 'vendors/products.html', {'vendor': vendor, 'products': products})


@login_required
def vendor_product_add(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()
            messages.success(request, f'✅ "{product.name}" added!')
            return redirect('vendor_products')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = VendorProductForm()
    return render(request, 'vendors/product_form.html', {
        'vendor': vendor, 'form': form, 'action': 'Add'
    })


@login_required
def vendor_product_edit(request, pk):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ "{product.name}" updated!')
            return redirect('vendor_products')
    else:
        form = VendorProductForm(instance=product)
    return render(request, 'vendors/product_form.html', {
        'vendor': vendor, 'form': form, 'action': 'Edit', 'product': product
    })


@login_required
def vendor_product_delete(request, pk):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted.')
    return redirect('vendor_products')


@login_required
def vendor_packages(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    packages = vendor.packages.all().order_by('-created_at')
    return render(request, 'vendors/packages.html', {'vendor': vendor, 'packages': packages})


@login_required
def vendor_package_add(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    vendor_products = vendor.products.filter(is_active=True)
    if request.method == 'POST':
        form = VendorPackageForm(request.POST, request.FILES)
        product_ids = request.POST.getlist('package_products')
        if form.is_valid():
            with transaction.atomic():
                pkg = form.save(commit=False)
                pkg.vendor = vendor
                pkg.save()
                for pid in product_ids:
                    try:
                        p = Product.objects.get(pk=pid, vendor=vendor)
                        PackageItem.objects.create(package=pkg, product=p, quantity=1)
                    except Product.DoesNotExist:
                        pass
            messages.success(request, f'✅ Package "{pkg.name}" created!')
            return redirect('vendor_packages')
    else:
        form = VendorPackageForm()
    return render(request, 'vendors/package_form.html', {
        'vendor': vendor, 'form': form,
        'vendor_products': vendor_products,
        'selected_ids': [],
        'action': 'Create'
    })


@login_required
def vendor_package_edit(request, pk):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    pkg = get_object_or_404(BTSPackage, pk=pk, vendor=vendor)
    vendor_products = vendor.products.filter(is_active=True)
    selected_ids = list(pkg.package_items.values_list('product_id', flat=True))
    if request.method == 'POST':
        form = VendorPackageForm(request.POST, request.FILES, instance=pkg)
        product_ids = request.POST.getlist('package_products')
        if form.is_valid():
            with transaction.atomic():
                form.save()
                pkg.package_items.all().delete()
                for pid in product_ids:
                    try:
                        p = Product.objects.get(pk=pid, vendor=vendor)
                        PackageItem.objects.create(package=pkg, product=p, quantity=1)
                    except Product.DoesNotExist:
                        pass
            messages.success(request, f'✅ Package "{pkg.name}" updated!')
            return redirect('vendor_packages')
    else:
        form = VendorPackageForm(instance=pkg)
    return render(request, 'vendors/package_form.html', {
        'vendor': vendor, 'form': form, 'package': pkg,
        'vendor_products': vendor_products,
        'selected_ids': selected_ids, 'action': 'Edit'
    })


@login_required
def vendor_orders(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    orders = Order.objects.filter(
        items__product__vendor=vendor
    ).distinct().order_by('-created_at')
    return render(request, 'vendors/orders.html', {'vendor': vendor, 'orders': orders})


@login_required
def vendor_order_detail(request, order_number):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    order = get_object_or_404(Order, order_number=order_number)
    vendor_items = order.items.filter(product__vendor=vendor)
    return render(request, 'vendors/order_detail.html', {
        'vendor': vendor, 'order': order, 'vendor_items': vendor_items
    })


@login_required
def vendor_settings(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Store settings updated!')
            return redirect('vendor_settings')
    else:
        form = VendorRegistrationForm(instance=vendor)
    return render(request, 'vendors/settings.html', {'vendor': vendor, 'form': form})


def vendor_storefront(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug, status='active')
    products = vendor.products.filter(is_active=True)
    packages = vendor.packages.filter(is_active=True)
    return render(request, 'vendors/storefront.html', {
        'vendor': vendor, 'products': products, 'packages': packages
    })
