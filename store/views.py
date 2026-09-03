from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, hmac, hashlib
import requests as req_lib
from .models import (
    Category, PartnerBrand, Product, BTSPackage,
    Cart, CartItem, Order, OrderItem, Wishlist, WishlistItem
)


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(customer=request.user, defaults={'session_key': ''})
    else:
        key = request.session.session_key
        if not key:
            request.session.create()
            key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=key, customer=None)
    return cart


def home(request):
    featured_packages = BTSPackage.objects.filter(is_active=True, is_featured=True)[:3]
    all_packages      = BTSPackage.objects.filter(is_active=True)[:6]
    categories        = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    partner_brands    = PartnerBrand.objects.filter(is_featured=True)[:6]
    return render(request, 'store/home.html', {
        'featured_packages': featured_packages,
        'all_packages':      all_packages,
        'categories':        categories,
        'featured_products': featured_products,
        'partner_brands':    partner_brands,
        'min_custom_items':  settings.BTS_MIN_CUSTOM_ITEMS,
    })


def packages(request):
    tier   = request.GET.get('tier', '')
    gender = request.GET.get('gender', '')
    pkgs   = BTSPackage.objects.filter(is_active=True)
    if tier:
        pkgs = pkgs.filter(budget_tier=tier)
    if gender:
        pkgs = pkgs.filter(gender__in=[gender, 'both'])
    return render(request, 'store/packages.html', {
        'packages':      pkgs,
        'active_tier':   tier,
        'active_gender': gender,
    })


def _parse_items_list(items_list_text):
    """
    Parse items list text into structured items with colors and sizes.
    Format: Item Name [colors: Red, Blue] [sizes: S, M, L]
    """
    import re
    items = []
    for line in items_list_text.splitlines():
        line = line.strip()
        if not line:
            continue

        item = {'name': line, 'colors': [], 'sizes': []}

        # Extract colors
        colors_match = re.search(r'\[colors:\s*([^\]]+)\]', line, re.IGNORECASE)
        if colors_match:
            item['colors'] = [c.strip() for c in colors_match.group(1).split(',')]
            line = re.sub(r'\[colors:[^\]]+\]', '', line, flags=re.IGNORECASE).strip()

        # Extract sizes
        sizes_match = re.search(r'\[sizes:\s*([^\]]+)\]', line, re.IGNORECASE)
        if sizes_match:
            item['sizes'] = [s.strip() for s in sizes_match.group(1).split(',')]
            line = re.sub(r'\[sizes:[^\]]+\]', '', line, flags=re.IGNORECASE).strip()

        item['name'] = line.strip()
        items.append(item)

    return items


def package_detail(request, slug):
    pkg     = get_object_or_404(BTSPackage, slug=slug, is_active=True)
    reviews = pkg.reviews.all().order_by('-created_at')
    parsed_items = _parse_items_list(pkg.items_list) if pkg.items_list else []
    return render(request, 'store/package_detail.html', {
        'package':      pkg,
        'reviews':      reviews,
        'parsed_items': parsed_items,
    })


def build_your_own(request):
    categories    = Category.objects.all()
    category_slug = request.GET.get('category', '')
    search        = request.GET.get('q', '')
    products      = Product.objects.filter(is_active=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    cart = _get_or_create_cart(request)
    return render(request, 'store/build_your_own.html', {
        'products':        products,
        'categories':      categories,
        'cart':            cart,
        'min_items':       settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee':   settings.BTS_CUSTOM_PACKAGING_FEE,
        'active_category': category_slug,
    })


def shop_by_category(request):
    return render(request, 'store/categories.html', {'categories': Category.objects.all()})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products  = Product.objects.filter(category=category, is_active=True)
    return render(request, 'store/category_products.html', {
        'category': category,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related  = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    reviews  = product.reviews.all().order_by('-created_at')
    return render(request, 'store/product_detail.html', {
        'product':          product,
        'related_products': related,
        'reviews':          reviews,
    })


def partner_brands(request):
    return render(request, 'store/partner_brands.html', {'brands': PartnerBrand.objects.all()})


def brand_detail(request, slug):
    brand    = get_object_or_404(PartnerBrand, slug=slug)
    products = brand.products.filter(is_active=True)
    return render(request, 'store/brand_detail.html', {
        'brand': brand, 'products': products,
    })


def about(request):
    return render(request, 'store/about.html')


def faqs(request):
    return render(request, 'store/faqs.html', {
        'min_custom_items': settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee':    settings.BTS_CUSTOM_PACKAGING_FEE,
    })


def contact(request):
    return render(request, 'store/contact.html')


def cart_view(request):
    cart = _get_or_create_cart(request)
    return render(request, 'store/cart.html', {
        'cart':         cart,
        'min_items':    settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee': settings.BTS_CUSTOM_PACKAGING_FEE,
    })


def add_to_cart(request, item_type, item_id):
    cart = _get_or_create_cart(request)
    size = request.POST.get('size', '')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))

    if item_type == 'package':
        pkg = get_object_or_404(BTSPackage, id=item_id)
        selections = request.POST.get('selections', '')
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, package=pkg,
            defaults={'quantity': 1, 'selected_size': selections[:500] if selections else ''}
        )
        if not created and selections:
            cart_item.selected_size = selections[:500]
            cart_item.save()
        cart.cart_type = 'package'
        cart.save()
        messages.success(request, f'"{pkg.name}" added to cart!')
        return redirect('checkout_addons')

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
        messages.success(request, f'"{product.name}" added to cart!')

    return redirect(next_url)


def remove_from_cart(request, item_id):
    cart = _get_or_create_cart(request)
    CartItem.objects.filter(id=item_id, cart=cart).delete()
    messages.success(request, 'Item removed.')
    return redirect('cart')


def checkout_addons(request):
    """
    Optional step between cart and checkout.
    Shows individual products the customer can add to their package order.
    """
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        return redirect('cart')

    category_slug = request.GET.get('cat', '')
    addon_products = Product.objects.filter(is_active=True)
    if category_slug:
        addon_products = addon_products.filter(category__slug=category_slug)

    categories = Category.objects.all()

    return render(request, 'store/checkout_addons.html', {
        'cart':           cart,
        'addon_products': addon_products,
        'categories':     categories,
        'active_cat':     category_slug,
    })


@login_required
def checkout(request):
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    if not cart.can_checkout:
        messages.error(request, f'Add at least {settings.BTS_MIN_CUSTOM_ITEMS} items for a custom package.')
        return redirect('cart')

    if request.method == 'POST':
        full_name  = request.POST.get('full_name', '').strip()
        phone      = request.POST.get('phone', '').strip()
        street     = request.POST.get('street', '').strip()
        city       = request.POST.get('city', '').strip()
        state      = request.POST.get('state', '').strip()
        notes      = request.POST.get('notes', '').strip()
        fulfilment = request.POST.get('fulfilment', 'delivery')

        # Validate required fields
        if not full_name or not phone:
            messages.error(request, 'Please fill in your name and phone number.')
            return render(request, 'store/checkout.html', {'cart': cart, 'user': request.user})

        if fulfilment == 'delivery' and not all([street, city, state]):
            messages.error(request, 'Please fill in your delivery address.')
            return render(request, 'store/checkout.html', {'cart': cart, 'user': request.user})

        # Delivery fee
        if fulfilment == 'pickup':
            delivery_fee = 0
            shipping_address = 'PICKUP - BTS Consolidation Point, Ondo'
        else:
            delivery_zone = request.POST.get('delivery_zone', 'ondo_near')
            zone_fees = {
                'ondo_near':    950,
                'ondo_park':    1100,
                'ondo_far':     2200,
                'outside_ondo': 0,
            }
            delivery_fee = zone_fees.get(delivery_zone, 950)
            shipping_address = f"{street}, {city}, {state}"

        # 3% BTS Service Fee
        service_fee = int(round(float(cart.subtotal) * 0.03))
        grand_total = int(cart.total) + delivery_fee + service_fee

        order = Order.objects.create(
            customer=request.user,
            order_number=Order.generate_order_number(),
            status='pending',
            subtotal=cart.subtotal,
            packaging_fee=service_fee,
            delivery_fee=delivery_fee,
            total=grand_total,
            full_name=full_name,
            phone=phone,
            street=street,
            city=city,
            state=state,
            shipping_address=shipping_address,
            notes=('[PICKUP] ' + notes if fulfilment == 'pickup' else notes).strip(),
            payment_status='unpaid',
        )

        for ci in cart.items.all():
            name = ci.package.name if ci.package else ci.product.name
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                package=ci.package,
                product_name=name,
                quantity=ci.quantity,
                unit_price=ci.unit_price,
                selected_size=ci.selected_size,
            )

        cart.items.all().delete()
        return redirect('pay_order', order_number=order.order_number)

    return render(request, 'store/checkout.html', {
        'cart':          cart,
        'user':          request.user,
        'bts_commission': 2000,
    })


@login_required
def pay_order(request, order_number):
    order       = get_object_or_404(Order, order_number=order_number, customer=request.user)
    amount_kobo = int(order.total * 100)

    return render(request, 'store/pay.html', {
        'order':               order,
        'amount_kobo':         amount_kobo,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    })


@login_required
def payment_callback(request):
    reference = request.GET.get('reference', '')
    if not reference:
        messages.error(request, 'Payment reference missing.')
        return redirect('home')

    # Dev mode simulation
    if reference.startswith('TEST_'):
        order_number = reference.replace('TEST_', '')
        order = Order.objects.filter(order_number=order_number, customer=request.user).first()
        if order and order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.status         = 'confirmed'
            order.payment_reference = reference
            order.paid_at        = timezone.now()
            order.save()
            from .emails import send_order_confirmation, send_vendor_order_notification
            send_order_confirmation(order, request)
            send_vendor_order_notification(order)
            messages.success(request, f'Payment confirmed! Order #{order.order_number}')
            return redirect('order_confirmed', order_number=order.order_number)
        return redirect('home')

    # Real Paystack verification using requests library
    try:
        resp = req_lib.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers={
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            },
            timeout=30,
        )
        data = resp.json()
        print(f'[BTS] Paystack verify HTTP {resp.status_code}: {data}')

        if data.get('data', {}).get('status') == 'success':
            metadata     = data['data'].get('metadata', {})
            order_number = metadata.get('order_number', '')

            print(f'[BTS] Payment success. Reference: {reference}, Order: {order_number}')

            # Try multiple ways to find the order
            order = None
            try:
                order = Order.objects.get(payment_reference=reference)
            except Order.DoesNotExist:
                pass

            if not order and order_number:
                order = Order.objects.filter(order_number=order_number).first()

            if not order:
                # Last resort: find most recent unpaid order for this customer
                if request.user.is_authenticated:
                    order = Order.objects.filter(
                        customer=request.user,
                        payment_status='unpaid'
                    ).order_by('-created_at').first()

            if order and order.payment_status != 'paid':
                order.payment_status    = 'paid'
                order.status            = 'confirmed'
                order.payment_reference = reference
                order.paid_at           = timezone.now()
                order.save()
                _decrement_stock(order)
                try:
                    from .emails import send_order_confirmation, send_vendor_order_notification
                    send_order_confirmation(order, request)
                    send_vendor_order_notification(order)
                except Exception as email_err:
                    print(f'[BTS] Email error: {email_err}')
                messages.success(request, f'Payment successful! Order #{order.order_number} confirmed.')
                return redirect('order_confirmed', order_number=order.order_number)
            elif order and order.payment_status == 'paid':
                return redirect('order_confirmed', order_number=order.order_number)
            else:
                print(f'[BTS] Order not found for reference {reference}, order_number {order_number}')
                messages.error(request, 'Payment received but order not found. Please contact support with reference: ' + reference)
        else:
            print(f'[BTS] Paystack verification failed: {data}')
            messages.error(request, 'Payment verification failed. Please contact support.')
    except Exception as e:
        print(f'[BTS] Payment callback error: {e}')
        messages.error(request, 'Could not verify payment. Please contact support.')

    return redirect('home')


@csrf_exempt
def paystack_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    payload    = request.body
    sig_header = request.headers.get('X-Paystack-Signature', '')
    secret     = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    expected   = hmac.new(secret, payload, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        return JsonResponse({'status': 'invalid signature'}, status=400)

    event = json.loads(payload)
    if event.get('event') == 'charge.success':
        reference = event['data']['reference']
        try:
            order = Order.objects.get(payment_reference=reference)
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.status         = 'confirmed'
                order.paid_at        = timezone.now()
                order.save()
        except Order.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok'})


@login_required
def order_confirmed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'store/order_confirmed.html', {'order': order})


@login_required
def submit_review(request, product_slug=None, package_slug=None):
    rating = int(request.POST.get('rating', 5))
    title  = request.POST.get('title', '').strip()
    body   = request.POST.get('body', '').strip()

    if not title or not body:
        messages.error(request, 'Please fill in both title and review.')
    elif product_slug:
        from .models import Review
        product = get_object_or_404(Product, slug=product_slug)
        Review.objects.update_or_create(
            customer=request.user, product=product,
            defaults={'rating': rating, 'title': title, 'body': body}
        )
        messages.success(request, 'Review submitted!')
        return redirect('product_detail', slug=product_slug)
    elif package_slug:
        from .models import Review
        package = get_object_or_404(BTSPackage, slug=package_slug)
        Review.objects.update_or_create(
            customer=request.user, package=package,
            defaults={'rating': rating, 'title': title, 'body': body}
        )
        messages.success(request, 'Review submitted!')
        return redirect('package_detail', slug=package_slug)

    return redirect('home')


def _decrement_stock(order):
    """Reduce stock for each product in a paid order."""
    for item in order.items.all():
        if item.product and item.product.stock > 0:
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save(update_fields=['stock'])


def search(request):
    query    = request.GET.get('q', '').strip()
    packages = BTSPackage.objects.none()
    products = Product.objects.none()
    total    = 0
    if query:
        packages = BTSPackage.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
        total = packages.count() + products.count()
    return render(request, 'store/search.html', {
        'query': query, 'packages': packages,
        'products': products, 'total_results': total,
    })


@login_required
def order_tracking(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'store/order_tracking.html', {'order': order})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    from vendors.models import Vendor
    from accounts.models import Customer
    from django.db.models import Sum
    paid_orders = Order.objects.filter(payment_status='paid')
    paid_count  = paid_orders.count()
    total_rev   = paid_orders.aggregate(s=Sum('total'))['s'] or 0
    commission  = paid_count * 2000
    return render(request, 'store/admin_dashboard.html', {
        'total_revenue':     total_rev,
        'commission_total':  commission,
        'vendor_total':      total_rev - commission,
        'total_orders':      Order.objects.count(),
        'paid_orders_count': paid_count,
        'total_customers':   Customer.objects.filter(is_staff=False).count(),
        'total_vendors':     Vendor.objects.filter(status='active').count(),
        'total_products':    Product.objects.filter(is_active=True).count(),
        'total_packages':    BTSPackage.objects.filter(is_active=True).count(),
        'recent_orders':     Order.objects.order_by('-created_at')[:10],
        'top_vendors':       Vendor.objects.all()[:5],
    })


def sell_on_bts(request):
    benefits = [
        ('', 'Targeted Student Audience', 'BTS is built exclusively for Nigerian university students — your products reach exactly who needs them.'),
        ('', 'Create BTS Packages', 'Bundle your products into Essential, Glow, or Complete sets. Packages sell faster than individual items.'),
        ('', 'Full Sales Dashboard', 'Track your products, orders, and revenue in real time from your vendor dashboard.'),
        ('', 'Instant Order Alerts', 'Get notified by email the moment a customer buys your product.'),
        ('', 'Nationwide Reach', 'BTS delivers to all 36 states in Nigeria.'),
        ('', 'Secure Payments', 'All payments processed securely via Paystack. No cash, no risk.'),
    ]
    return render(request, 'store/sell_on_bts.html', {'benefits': benefits})


def terms(request):
    return render(request, 'store/terms.html')


def privacy(request):
    return render(request, 'store/privacy.html')


def refund_policy(request):
    return render(request, 'store/refund.html')


@login_required
def wishlist(request):
    wl, _ = Wishlist.objects.get_or_create(customer=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wl})