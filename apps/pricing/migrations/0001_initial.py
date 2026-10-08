import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PricingTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=90, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="TierPrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("minimum_quantity", models.PositiveSmallIntegerField(default=1)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("tier", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prices", to="pricing.pricingtier")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tier_prices", to="catalog.variant")),
            ],
            options={"ordering": ["tier_id", "variant_id", "minimum_quantity"]},
        ),
        migrations.CreateModel(
            name="UserPricingTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=12)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_pricing_assignments", to=settings.AUTH_USER_MODEL)),
                ("tier", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_assignments", to="pricing.pricingtier")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pricing_assignment", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "user pricing tier assignment", "verbose_name_plural": "user pricing tier assignments"},
        ),
        migrations.AddConstraint(
            model_name="tierprice",
            constraint=models.UniqueConstraint(fields=("tier", "variant", "minimum_quantity"), name="unique_tier_variant_min_qty"),
        ),
        migrations.AddConstraint(
            model_name="tierprice",
            constraint=models.CheckConstraint(condition=Q(minimum_quantity__gte=1), name="tier_price_min_qty_gte_1"),
        ),
        migrations.AddConstraint(
            model_name="tierprice",
            constraint=models.CheckConstraint(condition=Q(unit_price__gt=0), name="tier_price_positive"),
        ),

    ]
