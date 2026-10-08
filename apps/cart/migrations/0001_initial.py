import django.db.models.deletion
from django.conf import settings
from django.db import migrations,models

class Migration(migrations.Migration):
    initial=True
    dependencies=[("catalog","0001_initial"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
      migrations.CreateModel(name="Cart",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("updated_at",models.DateTimeField(auto_now=True)),("user",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="cart",to=settings.AUTH_USER_MODEL))]),
      migrations.CreateModel(name="CartItem",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("quantity",models.PositiveSmallIntegerField()),("cart",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="items",to="cart.cart")),("variant",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to="catalog.variant"))]),
      migrations.AddConstraint(model_name="cartitem",constraint=models.UniqueConstraint(fields=("cart","variant"),name="unique_variant_per_cart")),
      migrations.AddConstraint(model_name="cartitem",constraint=models.CheckConstraint(condition=models.Q(quantity__gte=1,quantity__lte=20),name="cart_qty_1_to_20")),
    ]
