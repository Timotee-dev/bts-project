from django.conf import settings
from .models import Cart


def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(customer=request.user).first()
        else:
            key = request.session.session_key
            cart = Cart.objects.filter(session_key=key, customer=None).first() if key else None
        if cart:
            count = cart.total_items
    except Exception:
        pass
    return {'cart_item_count': count}


def site_settings(request):
    """Make key settings available to all templates."""
    return {
        'PAYSTACK_PUBLIC_KEY': settings.PAYSTACK_PUBLIC_KEY,
        'BTS_MIN_CUSTOM_ITEMS': settings.BTS_MIN_CUSTOM_ITEMS,
        'BTS_CUSTOM_PACKAGING_FEE': settings.BTS_CUSTOM_PACKAGING_FEE,
        'DEBUG': settings.DEBUG,
    }
