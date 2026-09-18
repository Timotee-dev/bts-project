"""
BTS Project — Email sending utilities
"""
from django.core.mail import EmailMultiAlternatives
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

    first_name = order.full_name.split()[0] if order.full_name else 'there'

    subject = f'Order Confirmed! #{order.order_number} — BTS Project'
    from_email = 'Naomi from BTS <arifalotimothy@gmail.com>'
    to_email = order.customer.email

    text_content = f"""Hi {first_name}! 💚

Welcome to BTS PROJECT '26! 🎉

Thank you so much for shopping with us. Your order has been received, and we're getting your BTS package ready for you.

Your physical package will be delivered to you soon, and we'll keep you updated as it makes its way to you. 📦

Butttt… your BTS experience doesn't stop at the box. 👀

YOU JUST UNLOCKED YOUR BTS FRESHER STARTER BUNDLE 💚📦

Your BTS Fresher Starter Bundle gives you access to the additional resources and student experiences that come with your package — from fresher guidance and practical student resources to style, money tips, community access and more, depending on your package.

Basically:
You shop. We sort the essentials. Then we help you navigate the rest.

READY TO UNLOCK IT?

Click the link below to activate your BTS Fresher Starter Bundle:
https://wa.me/2349052384844

Once you click, you'll be taken through the next step to verify your purchase and get access to your bundle.

Keep your order details handy: Order #{order.order_number}

We're excited to have you on this journey with us. 💚📦

Naomi from BTS
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
.container {{ max-width: 600px; margin: 0 auto; background: white; }}
.header {{ background: #1a4a2e; padding: 32px 24px; text-align: center; }}
.header img {{ height: 48px; }}
.body {{ padding: 32px 24px; }}
.cta {{ display: block; background: #1a4a2e; color: white !important; text-decoration: none; padding: 16px 32px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 16px; margin: 24px 0; }}
.footer {{ background: #1a4a2e; color: rgba(255,255,255,0.7); padding: 20px 24px; text-align: center; font-size: 12px; }}
h1 {{ color: #1a4a2e; }}
p {{ color: #333; line-height: 1.7; }}
</style></head>
<body>
<div class="container">
  <div class="header">
    <h2 style="color:white;margin:0;">BTS PROJECT '26 💚</h2>
  </div>
  <div class="body">
    <h1>Hi {first_name}! 💚</h1>
    <p>Welcome to <strong>BTS PROJECT '26!</strong> 🎉</p>
    <p>Thank you so much for shopping with us. Your order has been received, and we're getting your BTS package ready for you.</p>
    <p>Your physical package will be delivered to you soon, and we'll keep you updated as it makes its way to you. 📦</p>
    <p>Butttt… your BTS experience doesn't stop at the box. 👀</p>
    <h2 style="color:#1a4a2e;">YOU JUST UNLOCKED YOUR BTS FRESHER STARTER BUNDLE 💚📦</h2>
    <p>Your BTS Fresher Starter Bundle gives you access to the additional resources and student experiences that come with your package — from fresher guidance and practical student resources to style, money tips, community access and more, depending on your package.</p>
    <p><strong>Basically:</strong><br>You shop. We sort the essentials. Then we help you navigate the rest.</p>
    <p><strong>READY TO UNLOCK IT?</strong></p>
    <p>Click the button below to activate your BTS Fresher Starter Bundle.</p>
    <a href="https://wa.me/2349052384844" class="cta">ACTIVATE MY BTS FRESHER STARTER BUNDLE →</a>
    <p style="color:#666;font-size:13px;">Once you click, you'll be taken through the next step to verify your purchase and get access to your bundle. Keep your order details handy — Order <strong>#{order.order_number}</strong></p>
    <p>We're excited to have you on this journey with us. 💚📦</p>
    <p><strong>Naomi from BTS</strong></p>
  </div>
  <div class="footer">
    <p>BTS Project '26 &nbsp;|&nbsp; <a href="https://instagram.com/the_btsproject" style="color:rgba(255,255,255,0.7);">@the_btsproject</a></p>
  </div>
</div>
</body></html>"""

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        import traceback
        print(f'[BTS] Order confirmation email failed for #{order.order_number}: {e}')
        print(traceback.format_exc())
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

            subject = f'🛍️ New Order #{order.order_number} — BTS Project'
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