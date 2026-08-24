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
from .emails import send_order_confirmation, send_vendor_order_notification
from .delivery import get_delivery_fee
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
    all_packages = BTSPackage.objects.filter(is_active=True)[:6]
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    partner_brands = PartnerBrand.objects.filter(is_featured=True)[:6]
    return render(request, 'store/home.html', {
        'featured_packages': featured_packages,
        'all_packages': all_packages,
        'categories': categories,
        'featured_products': featured_products,
        'partner_brands': partner_brands,
        'min_custom_items': settings.BTS_MIN_CUSTOM_ITEMS,
    })


def packages(request):
    tier = request.GET.get('tier', '')
    pkgs = BTSPackage.objects.filter(is_active=True)
    if tier:
        pkgs = pkgs.filter(budget_tier=tier)
    return render(request, 'store/packages.html', {
        'packages': pkgs, 'active_tier': tier,
    })


def package_detail(request, slug):
    pkg = get_object_or_404(BTSPackage, slug=slug, is_active=True)
    reviews = pkg.reviews.all().order_by('-created_at')
    return render(request, 'store/package_detail.html', {
        'package': pkg, 'reviews': reviews,
    })


def build_your_own(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '')
    search = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    cart = _get_or_create_cart(request)
    return render(request, 'store/build_your_own.html', {
        'products': products, 'categories': categories, 'cart': cart,
        'min_items': settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee': settings.BTS_CUSTOM_PACKAGING_FEE,
        'active_category': category_slug,
    })


def shop_by_category(request):
    return render(request, 'store/categories.html', {'categories': Category.objects.all()})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'store/category_products.html', {
        'category': category, 'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    reviews = product.reviews.all().order_by('-created_at')
    return render(request, 'store/product_detail.html', {
        'product': product, 'related_products': related, 'reviews': reviews,
    })


def partner_brands(request):
    return render(request, 'store/partner_brands.html', {'brands': PartnerBrand.objects.all()})


def brand_detail(request, slug):
    brand = get_object_or_404(PartnerBrand, slug=slug)
    return render(request, 'store/brand_detail.html', {
        'brand': brand, 'products': brand.products.filter(is_active=True),
    })


def about(request):
    return render(request, 'store/about.html')


def faqs(request):
    return render(request, 'store/faqs.html', {
        'min_custom_items': settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee': settings.BTS_CUSTOM_PACKAGING_FEE,
    })


def contact(request):
    return render(request, 'store/contact.html')


def cart_view(request):
    cart = _get_or_create_cart(request)
    return render(request, 'store/cart.html', {
        'cart': cart,
        'min_items': settings.BTS_MIN_CUSTOM_ITEMS,
        'packaging_fee': settings.BTS_CUSTOM_PACKAGING_FEE,
    })


def add_to_cart(request, item_type, item_id):
    cart = _get_or_create_cart(request)
    size = request.POST.get('size', '')
    if item_type == 'package':
        pkg = get_object_or_404(BTSPackage, id=item_id)
        CartItem.objects.get_or_create(cart=cart, package=pkg, defaults={'quantity': 1})
        cart.cart_type = 'package'
        cart.save()
        messages.success(request, f'"{pkg.name}" added to cart!')
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
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


def remove_from_cart(request, item_id):
    cart = _get_or_create_cart(request)
    CartItem.objects.filter(id=item_id, cart=cart).delete()
    messages.success(request, 'Item removed.')
    return redirect('cart')


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
        full_name    = request.POST.get('full_name', '').strip()
        phone        = request.POST.get('phone', '').strip()
        street       = request.POST.get('street', '').strip()
        city         = request.POST.get('city', '').strip()
        state        = request.POST.get('state', '').strip()
        notes        = request.POST.get('notes', '').strip()

        if not all([full_name, phone, street, city, state]):
            messages.error(request, 'Please fill in all delivery fields.')
            return render(request, 'store/checkout.html', {'cart': cart})

        # Calculate delivery fee
        delivery_fee = get_delivery_fee(state)
        grand_total = cart.total + delivery_fee

        # Create the order (pending payment)
        order = Order.objects.create(
            customer=request.user,
            order_number=Order.generate_order_number(),
            status='pending',
            subtotal=cart.subtotal,
            packaging_fee=cart.packaging_fee,
            delivery_fee=delivery_fee,
            total=grand_total,
            full_name=full_name,
            phone=phone,
            street=street,
            city=city,
            state=state,
            shipping_address=f"{street}, {city}, {state}",
            notes=notes,
            payment_status='unpaid',
        )

        # Copy cart items to order
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

        # Clear cart
        cart.items.all().delete()

        # Redirect to Paystack payment page
        return redirect('pay_order', order_number=order.order_number)

    from .delivery import get_all_states_with_fees
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'user': request.user,
        'states_with_fees': get_all_states_with_fees(),
    })


@login_required
def pay_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    # Amount in kobo for Paystack
    amount_kobo = int(order.total * 100)
    return render(request, 'store/pay.html', {
        'order': order,
        'amount_kobo': amount_kobo,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    })


@login_required
def payment_callback(request):
    """Paystack redirects here after payment."""
    reference = request.GET.get('reference', '')
    if not reference:
        messages.error(request, 'Payment reference missing.')
        return redirect('home')

    # Dev mode: simulate payment success for TEST_ references
    if reference.startswith('TEST_'):
        order_number = reference.replace('TEST_', '')
        order = Order.objects.filter(order_number=order_number, customer=request.user).first()
        if order and order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.payment_reference = reference
            order.paid_at = timezone.now()
            order.save()
            send_order_confirmation(order, request)
            send_vendor_order_notification(order)
            messages.success(request, f'(Dev) Payment simulated! Order #{order.order_number} confirmed.')
            return redirect('order_confirmed', order_number=order.order_number)
        return redirect('home')

    # Verify with Paystack API
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers={'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

        if data.get('data', {}).get('status') == 'success':
            metadata = data['data'].get('metadata', {})
            order_number = metadata.get('order_number') or data['data'].get('reference', '').split('_')[0]

            # Find order by reference
            try:
                order = Order.objects.get(payment_reference=reference)
            except Order.DoesNotExist:
                # Fallback: find by order_number in metadata
                order_number = metadata.get('order_number', '')
                order = Order.objects.filter(order_number=order_number, customer=request.user).first()

            if order and order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.payment_reference = reference
                order.paid_at = timezone.now()
                order.save()
                messages.success(request, f'Payment successful! Order #{order.order_number} confirmed.')
                return redirect('order_confirmed', order_number=order.order_number)
        else:
            messages.error(request, 'Payment verification failed. Please contact support.')
    except Exception as e:
        messages.error(request, f'Could not verify payment. Please contact support.')

    return redirect('home')


@csrf_exempt
def paystack_webhook(request):
    """Paystack sends webhook events here."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    payload = request.body
    sig_header = request.headers.get('X-Paystack-Signature', '')
    secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    expected = hmac.new(secret, payload, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        return JsonResponse({'status': 'invalid signature'}, status=400)

    event = json.loads(payload)
    if event.get('event') == 'charge.success':
        reference = event['data']['reference']
        try:
            order = Order.objects.get(payment_reference=reference)
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.paid_at = timezone.now()
                order.save()
        except Order.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok'})


@login_required
def order_confirmed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'store/order_confirmed.html', {'order': order})


@login_required
@require_POST
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
        messages.success(request, 'Review submitted! Thank you.')
        return redirect('product_detail', slug=product_slug)
    elif package_slug:
        from .models import Review
        package = get_object_or_404(BTSPackage, slug=package_slug)
        Review.objects.update_or_create(
            customer=request.user, package=package,
            defaults={'rating': rating, 'title': title, 'body': body}
        )
        messages.success(request, 'Review submitted! Thank you.')
        return redirect('package_detail', slug=package_slug)

    return redirect('home')


def sell_on_bts(request):
    benefits = [
        ('🎯', 'Targeted Student Audience', 'BTS is built exclusively for Nigerian university students — your products reach the exact people who need them most.'),
        ('📦', 'Create BTS Packages', 'Bundle your products into packages. Students love bundles and they sell faster than individual items.'),
        ('📊', 'Full Sales Dashboard', 'Track your products, orders, and monthly revenue in real time from your vendor dashboard.'),
        ('🔔', 'Instant Order Alerts', 'Get notified by email the moment a customer buys your product.'),
        ('🌍', 'Nationwide Reach', 'BTS delivers to all 36 states in Nigeria — your products reach students everywhere.'),
        ('💳', 'Secure Payments', 'All payments are processed securely via Paystack. No cash, no risk.'),
    ]
    return render(request, 'store/sell_on_bts.html', {'benefits': benefits})


@login_required
def wishlist(request):
    wl, _ = Wishlist.objects.get_or_create(customer=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wl})
