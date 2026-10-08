import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations,models

class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
      migrations.CreateModel(name="Order",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("public_id",models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),("status",models.CharField(choices=[("pending_payment","Pending payment"),("paid","Paid"),("cancelled","Cancelled")],default="pending_payment",max_length=24)),("total",models.DecimalField(decimal_places=2,max_digits=12)),("currency",models.CharField(default="NGN",max_length=3)),("expires_at",models.DateTimeField()),("created_at",models.DateTimeField(auto_now_add=True)),("user",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="orders",to=settings.AUTH_USER_MODEL))]),
      migrations.CreateModel(name="OrderItem",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("sku",models.CharField(max_length=64)),("product_name",models.CharField(max_length=160)),("unit_price",models.DecimalField(decimal_places=2,max_digits=10)),("quantity",models.PositiveSmallIntegerField()),("order",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="items",to="orders.order"))]),
    ]
