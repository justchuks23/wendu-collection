from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import Variant
from .models import StockLevel


@receiver(post_save, sender=Variant)
def ensure_stock_row(sender, instance, created, **kwargs):
    StockLevel.objects.get_or_create(variant=instance)
