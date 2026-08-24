from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Vendor(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor'
    )
    business_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='vendor_banners/', blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    # Bank details for payouts (recorded but BTS collects all via Paystack)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    account_name = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_verified = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    # Storefront settings
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name

    @property
    def total_sales(self):
        from store.models import OrderItem
        items = OrderItem.objects.filter(
            product__vendor=self,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        )
        return sum(i.line_total for i in items)

    @property
    def total_orders(self):
        from store.models import OrderItem
        return OrderItem.objects.filter(
            product__vendor=self
        ).values('order').distinct().count()

    @property
    def total_products(self):
        return self.products.filter(is_active=True).count()
