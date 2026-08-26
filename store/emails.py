"""
BTS Project — Email sending utilities
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_order_confirmation(order, request=None):
    """
    Send order confirmation email to the customer.
    Called immediately after payment is verified.
    """
    if not order.customer or not order.customer.email:
        return False

    site_url = 'http://127.0.0.1:8000'
    if request:
        site_url = request.build_absolute_uri('/').rstrip('/')

    context = {
        'order': order,
        'site_url': site_url,
    }

    subject = f'Order Confirmed! #{order.order_number} — BTS Project'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.customer.email

    # Render both versions
    text_content = render_to_string('emails/order_confirmation.txt', context)
    html_content = render_to_string('emails/order_confirmation.html', context)

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        # Never crash the order flow because of email failure
        print(f'[BTS] Order confirmation email failed for #{order.order_number}: {e}')
        return False


def send_vendor_order_notification(order):
    """
    Notify each vendor whose products are in this order.
    """
    from store.models import OrderItem
    from vendors.models import Vendor

    # Find all vendors with items in this order
    vendor_ids = OrderItem.objects.filter(
        order=order,
        product__vendor__isnull=False
    ).values_list('product__vendor_id', flat=True).distinct()

    for vendor_id in vendor_ids:
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
            if not vendor.email:
                continue

            # Get only this vendor's items
            vendor_items = order.items.filter(product__vendor=vendor)

            subject = f'New Order #{order.order_number} — BTS Project'
            text = f"""Hi {vendor.business_name},

You have a new order on BTS Project!

Order Number: #{order.order_number}
Customer: {order.full_name}
Delivery: {order.shipping_address}

YOUR ITEMS:
"""
            for item in vendor_items:
                text += f"- {item.product_name} x{item.quantity} — ₦{item.line_total}\n"

            text += f"""
Please prepare these items for pickup/delivery.

Log in to your vendor dashboard to view full details:
http://127.0.0.1:8000/vendors/orders/{order.order_number}/

The BTS Project Team
"""
            from django.core.mail import send_mail
            send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=True)

        except Exception as e:
            print(f'[BTS] Vendor notification failed for vendor {vendor_id}: {e}')


def send_order_status_update(order):
    """
    Email customer when vendor updates order status to processing, shipped, or delivered.
    """
    if not order.customer or not order.customer.email:
        return False

    status_messages = {
        'processing': (
            'Your order is being prepared',
            'The vendor is packing your items and will ship soon.'
        ),
        'shipped': (
            'Your order is on its way',
            'Your BTS package has been shipped and is heading to you. Check your delivery address below.'
        ),
        'delivered': (
            'Your order has been delivered',
            'Your BTS package has been delivered. We hope you love everything!'
        ),
    }

    subject_suffix, body_line = status_messages.get(
        order.status,
        ('Order Update', 'Your order status has been updated.')
    )

    subject  = f'BTS Project: {subject_suffix} — Order #{order.order_number}'
    message  = f"""Hi {order.full_name},

{body_line}

Order Details:
  Order Number : #{order.order_number}
  Status       : {order.get_status_display()}
  Delivery To  : {order.shipping_address}
  Phone        : {order.phone}

If you have any questions, contact us via our website or WhatsApp.

The BTS Project Team
"""
    from django.core.mail import send_mail
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f'[BTS] Status update email failed for #{order.order_number}: {e}')
        return False