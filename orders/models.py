from django.db import models
from backend.models import BaseModel
from users.models import User
from product.models import ProductVariant
from django.utils import timezone
from io import BytesIO
from reportlab.pdfgen import canvas
import uuid

class Order(BaseModel):
    """Stores the overall order for a user."""

    PENDING = 'PENDING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELED = 'CANCELED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SHIPPED, 'Shipped'), 
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Canceled'),
    ]
    order_number = models.CharField(max_length=100, unique=True, null=False, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    total_price = models.FloatField(default=0.0)
    time_duration = models.DurationField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Razorpayment Integration
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Auto-generate order number if not already set
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Order {self.id} by {self.user.email}"
    
    def valid_time(self):
        """
        Validates if the current time is within the `time_duration` window since `updated_at`.
        Returns True if the payment is still valid (within time window), False if time has expired.
        """
        # Calculate the expiration time by adding the time_duration to updated_at
        if self.time_duration:
            expiration_time = self.updated_at + self.time_duration

            # Check if the current time is beyond the expiration time
            return timezone.now() <= expiration_time
        else:
            return False
    
    def generate_invoice(self):
        """
        Generate a PDF invoice for the order.
        Returns a BytesIO stream containing the PDF content.
        """
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        # Invoice details
        pdf.drawString(100, 800, f"Invoice for Order: {self.order_number}")
        pdf.drawString(100, 780, f"Customer: {self.user.email}")
        pdf.drawString(100, 760, f"Total Price: {self.total_price}")
        pdf.drawString(100, 740, f"Order Status: {self.status}")

        # Add order items
        y_position = 700
        for item in self.items.all():
            pdf.drawString(100, y_position, f"Product: {item.product_variant.product.product_type.name}, Quantity: {item.quantity}, Price: {item.product_variant.price}")
            y_position -= 20

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer

    class Meta:
        db_table = "order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"


class OrderItem(BaseModel):
    """Stores the items in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Order Item {self.product_variant.product.code} (Order {self.order.id})"
    
    class Meta:
        db_table = "order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"


class Notification(BaseModel):
    """Stores notifications related to an order's payment process."""
    
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    DECLINED = 'DECLINED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (DECLINED, 'Declined'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    token_payment = models.FloatField()
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="sent_notifications", null=True)
    receiver = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    is_admin_read = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for Order {self.order.id} - Sender: {self.sender}"

    class Meta:
        db_table = "notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

class Selling(BaseModel):
    """Tracks sold variants along with order details."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="selling_order")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="sold_variant")
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Sold {self.quantity} of {self.product_variant.product.product_type} in Order {self.order.id}"
    
    class Meta:
        db_table = "selling"
        verbose_name = "Selling"
        verbose_name_plural = "Sellings"