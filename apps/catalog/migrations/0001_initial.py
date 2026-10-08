import uuid
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
      migrations.CreateModel(name="Category",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("name",models.CharField(max_length=80,unique=True)),("slug",models.SlugField(max_length=90,unique=True))]),
      migrations.CreateModel(name="Product",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("public_id",models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),("name",models.CharField(max_length=160)),("slug",models.SlugField(max_length=180,unique=True)),("description",models.TextField(max_length=3000)),("image_url",models.URLField(blank=True,max_length=500)),("is_active",models.BooleanField(default=False)),("featured",models.BooleanField(default=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("category",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="products",to="catalog.category"))]),
      migrations.CreateModel(name="Variant",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("public_id",models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),("sku",models.CharField(max_length=64,unique=True)),("size",models.CharField(blank=True,max_length=32)),("color",models.CharField(blank=True,max_length=48)),("price",models.DecimalField(decimal_places=2,max_digits=10)),("is_active",models.BooleanField(default=True)),("product",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="variants",to="catalog.product"))]),
      migrations.AddIndex(model_name="product",index=models.Index(fields=["is_active","featured"],name="catalog_prod_active_idx")),
    ]
