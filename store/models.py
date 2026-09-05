from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']


class PartnerBrand(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField()
    categories = models.ManyToManyField(Category, blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey(PartnerBrand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    # Vendor link — who sells this product
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='products'
    )

    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    available_colors = models.CharField(max_length=300, blank=True, help_text='Comma-separated colors e.g. Black, White, Navy Blue')
    available_sizes  = models.CharField(max_length=200, blank=True)
    stock = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def sizes_list(self):
        if self.available_sizes:
            return [s.strip() for s in self.available_sizes.split(',')]
        return []

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0


class BTSPackage(models.Model):
    BUDGET_CHOICES = [
        ('essential', 'Essential Set'),
        ('glow',      'Glow Set'),
        ('complete',  'Complete Set'),
    ]

    GENDER_CHOICES = [
        ('female', 'Female'),
        ('male',   'Male'),
        ('both',   'Both / Unisex'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='packages/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    budget_tier = models.CharField(max_length=20, choices=BUDGET_CHOICES, default='essential')
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, default='female')
    items_list  = models.TextField(blank=True, help_text="One item per line")
    products = models.ManyToManyField(Product, through='PackageItem')

    # Vendor who created this package (null = platform package)
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='packages'
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while BTSPackage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def savings(self):
        return self.original_price - self.price

    @property
    def savings_percent(self):
        if self.original_price > 0:
            return round((self.savings / self.original_price) * 100)
        return 0

    class Meta:
        ordering = ['order', 'price']


class PackageItem(models.Model):
    package = models.ForeignKey(BTSPackage, on_delete=models.CASCADE, related_name='package_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.package.name} - {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    package = models.ForeignKey(BTSPackage, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.rating}"


class Cart(models.Model):
    CART_TYPE_CHOICES = [('package', 'Package'), ('custom', 'Custom Build')]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    cart_type = models.CharField(max_length=20, choices=CART_TYPE_CHOICES, default='package')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def total_items(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def subtotal(self):
        return sum(i.line_total for i in self.items.all())

    @property
    def packaging_fee(self):
        return 0

    @property
    def total(self):
        return self.subtotal + self.packaging_fee

    @property
    def custom_item_count(self):
        return self.items.filter(package__isnull=True).count()

    @property
    def can_checkout(self):
        return self.items.exists()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(BTSPackage, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected_size = models.CharField(max_length=20, blank=True)

    def __str__(self):
        item = self.package or self.product
        return f"{item} x{self.quantity}"

    @property
    def unit_price(self):
        if self.package:
            return self.package.price
        return self.product.price if self.product else 0

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class PromoCode(models.Model):
    code            = models.CharField(max_length=50, unique=True)
    discount_type   = models.CharField(max_length=10, choices=[('percent','Percentage'),('fixed','Fixed Amount')], default='percent')
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2, help_text='Percentage (0-100) or fixed NGN amount')
    max_uses        = models.PositiveIntegerField(default=10)
    used_count      = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    valid_from      = models.DateTimeField(auto_now_add=True)
    valid_until     = models.DateTimeField(null=True, blank=True)
    applies_to_pkg  = models.ForeignKey('BTSPackage', null=True, blank=True, on_delete=models.SET_NULL, help_text='Leave blank to apply to any package')
    used_by         = models.ManyToManyField('accounts.Customer', blank=True, related_name='used_promos')

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percent' else 'NGN'})"

    @property
    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percent':
            return int(round(float(subtotal) * float(self.discount_value) / 100))
        else:
            return min(int(self.discount_value), int(subtotal))


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='orders'
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    packaging_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery info
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    street = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    shipping_address = models.TextField(blank=True)  # formatted full address

    # Payment
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_status = models.CharField(max_length=20, default='unpaid')
    paid_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number}"

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def generate_order_number():
        return 'BTS' + uuid.uuid4().hex[:8].upper()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(BTSPackage, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_size = models.CharField(max_length=20, blank=True)

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Wishlist(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist'
    )

    def __str__(self):
        return f"{self.customer.username}'s Wishlist"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(BTSPackage, on_delete=models.CASCADE, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)