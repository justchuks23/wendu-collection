import django.db.models.deletion
from django.conf import settings
from django.db import migrations,models
from django.db.models import F,Q

class Migration(migrations.Migration):
    initial=True
    dependencies=[("catalog","0001_initial"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
      migrations.CreateModel(name="StockLevel",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("quantity",models.PositiveIntegerField(default=0)),("reserved",models.PositiveIntegerField(default=0)),("updated_at",models.DateTimeField(auto_now=True)),("variant",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="stock",to="catalog.variant"))]),
      migrations.AddConstraint(model_name="stocklevel",constraint=models.CheckConstraint(condition=Q(quantity__gte=F("reserved")),name="stock_reserved_lte_quantity")),
      migrations.CreateModel(name="StockMovement",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("delta",models.IntegerField()),("reason",models.CharField(max_length=120)),("created_at",models.DateTimeField(auto_now_add=True)),("actor",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to=settings.AUTH_USER_MODEL)),("stock",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="movements",to="inventory.stocklevel"))]),
    ]
