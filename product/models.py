from django.db import models
from backend.models import BaseModel
from backend.utils import get_product_image_upload_path
from backend.utils import validate_file_size
from users.models import User
from django.utils import timezone 
from phonenumber_field.modelfields import PhoneNumberField

class ProductType(BaseModel):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

class BrandType(BaseModel):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

class ProductStyle(BaseModel):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

class Product(BaseModel):
    """Main product model to store common product attributes."""
    
    SEMIPREMIUM = 'SEMIPREMIUM'
    PREMIUM = 'PREMIUM'
    
    PRODUCT_CATEGORY_CHOICES = [
        ('SEMIPREMIUM', 'SEMIPREMIUM'),
        ('PREMIUM', 'PREMIUM'),
    ]
    
    ACTIVE = 1
    OUT_OF_STOCK = 2

    STATUSES = [
        (ACTIVE, "Active"),
        (OUT_OF_STOCK, "Out of stock"),
    ]

    product_category = models.CharField(max_length=20, choices=PRODUCT_CATEGORY_CHOICES, default='SEMIPRIMIUM')
    code = models.CharField(max_length=255, unique=True)
    product_type = models.ForeignKey('ProductType', on_delete=models.PROTECT, related_name="product_type")
    product_brand = models.ForeignKey('BrandType', on_delete=models.PROTECT, related_name="product_brand")
    product_style = models.ForeignKey('ProductStyle', on_delete=models.PROTECT, related_name="product_style")
    stones = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(choices=STATUSES, default=OUT_OF_STOCK)
    image = models.ImageField(
        upload_to=get_product_image_upload_path,
        blank=False,
        null=False,
        validators=[validate_file_size],
    )

    def __str__(self):
        return self.code

    class Meta:
        db_table = "product"
        verbose_name = "Product"


class Employee(BaseModel):
    first_name = models.CharField(max_length=255, null=True, blank=False)
    last_name = models.CharField(max_length=255, null=True, blank=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=False)
    phone_number = PhoneNumberField(
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
        unique=True,
        null=True, 
        blank=False
    )
    job_title = models.CharField(max_length=255, unique=True, null=True, blank=False)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_leaving = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    parent_name = models.CharField(max_length=255, null=True, blank=True)
    parent_address = models.TextField(null=True, blank=True)
    parent_mobile = PhoneNumberField(
        verbose_name="Parent's Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
        null=True, 
        blank=True
    )
    reference_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.email


class ProductVariant(BaseModel):
    """This model links a product color to different carat and price options."""

    PENDING = 'PENDING'
    INPROCESS = 'INPROCESS'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    
    QC_STATUS = [
        ('PENDING', 'PENDING'),
        ('INPROCESS', 'INPROCESS'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
    ]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="product_variant")
    color = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(
        upload_to=get_product_image_upload_path,
        blank=False,
        null=False,
        validators=[validate_file_size],
    )
    weight = models.FloatField(max_length=255, blank=True, null=False, default=10.0)
    size = models.FloatField(max_length=255, blank=True, null=False, default=7.5)
    carat = models.IntegerField()
    price = models.FloatField()
    quantity = models.IntegerField()
    notes = models.TextField(blank=True, null=True, default="")
    qc_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="product_variant_qc")
    qc_status = models.CharField(choices=QC_STATUS, default="PENDING")
    is_stock = models.BooleanField(default=False)

    def __str__(self):
        product_code = self.product.code
        product_color = self.color
        product_type_name = self.product.product_type.name
        return f"{product_code} - {product_type_name} - {product_color} - {self.carat} carat"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_product")

    def __str__(self):
        return f"Wish list for {self.user.email} - {self.product.code}"


class ShoppingCart(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shopping_cart")

    def __str__(self):
        return f"Shopping Cart for {self.user.email}"
   

class CartItems(BaseModel):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, null=False, blank=False, related_name="cart_items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_product_variant")
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Cart list for {self.cart.user.email} - {self.product_variant.product.code} - {self.product_variant.color}"
    
    class Meta:
        db_table = "cart"


class SharableCollection(BaseModel):
    slug = models.SlugField(max_length=250, db_index=True, unique=True, null=False, blank=False)
    product_variant_ids = models.TextField(null=False, blank=False)
    time_duration = models.DurationField(null=True, blank=True)
    is_validate = models.BooleanField(default=True)

    def __str__(self):
        return self.slug

    def valid_time(self):
        """
        Validates if the current time is within the `time_duration` window since `created_at`.
        Returns True if the payment is still valid (within time window), False if time has expired.
        """
        # Calculate the expiration time by adding the time_duration to created_at
        expiration_time = self.updated_at + self.time_duration

        # Check if the current time is beyond the expiration time
        return timezone.now() <= expiration_time
    