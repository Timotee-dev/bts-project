from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from store.models import Product, BTSPackage, PackageItem, Order, OrderItem
from .models import Vendor
from .forms import VendorRegistrationForm, VendorProductForm, VendorPackageForm


def vendor_register(request):
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
            messages.success(request, f'Welcome! Your store "{vendor.business_name}" is live.')
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
    try:
        return request.user.vendor
    except Exception:
        messages.error(request, "You don't have a vendor account yet.")
        return None


@login_required
def vendor_dashboard(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')

    from django.utils import timezone
    now = timezone.now()

    monthly_items = OrderItem.objects.filter(
        product__vendor=vendor,
        order__paid_at__year=now.year,
        order__paid_at__month=now.month,
        order__payment_status='paid',
    )
    monthly_revenue = sum(i.line_total for i in monthly_items)
    total_revenue   = sum(i.line_total for i in OrderItem.objects.filter(
        product__vendor=vendor, order__payment_status='paid',
    ))

    recent_orders = Order.objects.filter(
        items__product__vendor=vendor
    ).distinct().order_by('-created_at')[:8]

    top_products = vendor.products.filter(is_active=True).order_by('-created_at')[:5]

    return render(request, 'vendors/dashboard.html', {
        'vendor':          vendor,
        'recent_orders':   recent_orders,
        'top_products':    top_products,
        'monthly_revenue': monthly_revenue,
        'total_revenue':   total_revenue,
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
            messages.success(request, f'"{product.name}" added!')
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
            messages.success(request, f'"{product.name}" updated!')
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
    all_products = Product.objects.filter(is_active=True).order_by('category', 'name')

    if request.method == 'POST':
        name           = request.POST.get('name', '').strip()
        budget_tier    = request.POST.get('budget_tier', 'essential')
        gender         = request.POST.get('gender', 'female')
        description    = request.POST.get('description', '').strip()
        price          = request.POST.get('price', 0)
        original_price = request.POST.get('original_price', 0) or 0
        product_ids    = request.POST.getlist('package_products')

        if not name or not price:
            messages.error(request, 'Please fill in all required fields.')
        else:
            from django.utils.text import slugify
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            while BTSPackage.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            pkg = BTSPackage.objects.create(
                name=name,
                slug=slug,
                description=description,
                price=price,
                original_price=original_price or price,
                budget_tier=budget_tier,
                gender=gender,
                vendor=vendor,
                is_active=True,
            )
            if 'cover_image' in request.FILES:
                pkg.cover_image = request.FILES['cover_image']
                pkg.save()

            for pid in product_ids:
                try:
                    p = Product.objects.get(pk=pid)
                    PackageItem.objects.create(package=pkg, product=p, quantity=1)
                except Product.DoesNotExist:
                    pass

            messages.success(request, f'Package "{pkg.name}" created!')
            return redirect('vendor_packages')

    return render(request, 'vendors/package_form.html', {
        'vendor':          vendor,
        'vendor_products': all_products,
        'selected_ids':    [],
        'action':          'Create',
        'package':         None,
    })


@login_required
def vendor_package_edit(request, pk):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    pkg = get_object_or_404(BTSPackage, pk=pk, vendor=vendor)
    vendor_products = vendor.products.filter(is_active=True)
    selected_ids = list(pkg.package_items.values_list('product_id', flat=True))
    all_products = Product.objects.filter(is_active=True).order_by('category', 'name')
    selected_ids = list(pkg.package_items.values_list('product_id', flat=True))

    if request.method == 'POST':
        pkg.name           = request.POST.get('name', pkg.name).strip()
        pkg.budget_tier    = request.POST.get('budget_tier', pkg.budget_tier)
        pkg.gender         = request.POST.get('gender', pkg.gender)
        pkg.description    = request.POST.get('description', pkg.description).strip()
        pkg.price          = request.POST.get('price', pkg.price)
        pkg.original_price = request.POST.get('original_price', pkg.original_price) or pkg.price
        if 'cover_image' in request.FILES:
            pkg.cover_image = request.FILES['cover_image']
        pkg.save()

        product_ids = request.POST.getlist('package_products')
        pkg.package_items.all().delete()
        for pid in product_ids:
            try:
                p = Product.objects.get(pk=pid)
                PackageItem.objects.create(package=pkg, product=p, quantity=1)
            except Product.DoesNotExist:
                pass

        messages.success(request, f'Package "{pkg.name}" updated!')
        return redirect('vendor_packages')

    return render(request, 'vendors/package_form.html', {
        'vendor':          vendor,
        'package':         pkg,
        'vendor_products': all_products,
        'selected_ids':    selected_ids,
        'action':          'Edit',
    })


@login_required
def vendor_orders(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')

    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(
        items__product__vendor=vendor
    ).distinct().order_by('-created_at')

    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'vendors/orders.html', {
        'vendor': vendor,
        'orders': orders,
        'status_filter': status_filter,
    })


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
@require_POST
def vendor_update_order_status(request, order_number):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')

    order = get_object_or_404(Order, order_number=order_number)

    # Make sure this vendor has items in this order
    if not order.items.filter(product__vendor=vendor).exists():
        messages.error(request, 'You do not have items in this order.')
        return redirect('vendor_orders')

    new_status = request.POST.get('status', '')
    valid_transitions = {
        'confirmed':  'processing',
        'processing': 'shipped',
        'shipped':    'delivered',
    }

    if valid_transitions.get(order.status) == new_status:
        order.status = new_status
        order.save()
        # Notify customer
        try:
            from store.emails import send_order_status_update
            send_order_status_update(order)
        except Exception:
            pass
        messages.success(request, f'Order #{order.order_number} marked as {new_status}.')
    else:
        messages.error(request, 'Invalid status update.')

    return redirect('vendor_orders')


@login_required
def vendor_create_promo(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')

    if request.method == 'POST':
        from store.models import PromoCode, BTSPackage, Product
        import random, string

        code          = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percent')
        max_uses      = int(request.POST.get('max_uses', 10))
        valid_until   = request.POST.get('valid_until', '') or None
        target_type   = request.POST.get('target_type', '')
        target_id     = request.POST.get('target_id', '')

        # Handle discount value
        if discount_type == 'free':
            discount_value = 100
            discount_type  = 'percent'
        else:
            discount_value = float(request.POST.get('discount_value', 0))

        # Parse valid_until
        valid_until_dt = None
        if valid_until:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone
            valid_until_dt = parse_datetime(valid_until)

        # Link to package or product
        applies_to_pkg = None
        if target_type == 'package' and target_id:
            try:
                applies_to_pkg = BTSPackage.objects.get(pk=target_id, vendor=vendor)
            except BTSPackage.DoesNotExist:
                pass

        # Create promo
        try:
            PromoCode.objects.create(
                code           = code,
                discount_type  = discount_type,
                discount_value = discount_value,
                max_uses       = max_uses,
                valid_until    = valid_until_dt,
                applies_to_pkg = applies_to_pkg,
                is_active      = True,
            )
            messages.success(request, f'Promo code "{code}" created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating promo: {str(e)}')

        if target_type == 'package':
            return redirect('vendor_packages')
        return redirect('vendor_products')

    return redirect('vendor_packages')


@login_required
def vendor_settings(request):
    vendor = _get_vendor(request)
    if not vendor:
        return redirect('vendor_register')
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            vendor = form.save()
            # Retry Paystack subaccount if bank details were updated and no subaccount yet
            if not vendor.paystack_subaccount_code and vendor.bank_name and vendor.account_number:
                try:
                    from store.paystack_utils import create_vendor_subaccount
                    code = create_vendor_subaccount(vendor)
                    if code:
                        vendor.paystack_subaccount_code = code
                        vendor.save()
                        messages.success(request, 'Bank details saved and Paystack payments activated.')
                    else:
                        messages.success(request, 'Settings saved. Paystack subaccount creation pending.')
                except Exception:
                    messages.success(request, 'Settings saved.')
            else:
                messages.success(request, 'Store settings updated.')
            return redirect('vendor_settings')
    else:
        form = VendorRegistrationForm(instance=vendor)
    return render(request, 'vendors/settings.html', {'vendor': vendor, 'form': form})


def vendor_storefront(request, slug):
    vendor   = get_object_or_404(Vendor, slug=slug, status='active')
    products = vendor.products.filter(is_active=True)
    packages = vendor.packages.filter(is_active=True)
    return render(request, 'vendors/storefront.html', {
        'vendor': vendor, 'products': products, 'packages': packages
    })