from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import ProductVariant
from .models import Stock

@receiver(post_save, sender=ProductVariant)
def create_stock_for_variant(sender, instance, created, **kwargs):
    if created:
        # Create a Stock entry for each new ProductVariant
        Stock.objects.create(product_variant=instance)
