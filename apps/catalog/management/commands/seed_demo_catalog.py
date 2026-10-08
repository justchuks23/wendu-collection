from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Category, Product, Variant
from apps.inventory.models import StockLevel, StockMovement

PRODUCTS = [
    {
        "category": "Bags",
        "name": "The Weekend Carryall",
        "description": (
            "A roomy, structured carryall in soft-grain vegan leather. "
            "Built for long weekends and everyday plans."
        ),
        "image_url": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=1000&q=85",
        "sku": "BAG-WEEKEND-BRN",
        "size": "One size",
        "color": "Cognac",
        "price": "68500.00",
        "quantity": 12,
        "featured": True,
    },
    {
        "category": "Bags",
        "name": "Sculpted Leather Tote",
        "description": "An easy, clean-lined tote with room for the things you carry every day.",
        "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=1000&q=85",
        "sku": "BAG-SCULPT-BLK",
        "size": "One size",
        "color": "Black",
        "price": "92000.00",
        "quantity": 7,
        "featured": True,
    },
    {
        "category": "Shoes",
        "name": "Everyday Court Sneaker",
        "description": "A versatile low-profile sneaker with a cushioned footbed and soft lining.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1000&q=85",
        "sku": "SHOE-COURT-39",
        "size": "39",
        "color": "Cherry",
        "price": "57500.00",
        "quantity": 4,
        "featured": False,
    },
    {
        "category": "Shoes",
        "name": "City Strap Sandal",
        "description": "A refined, walkable sandal for sunny days and late dinners.",
        "image_url": "https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=1000&q=85",
        "sku": "SHOE-CITY-38",
        "size": "38",
        "color": "Sand",
        "price": "42000.00",
        "quantity": 9,
        "featured": False,
    },
    {
        "category": "Bags",
        "name": "Soft Form Crossbody",
        "description": "Hands-free, light and thoughtfully sized, with an adjustable strap.",
        "image_url": "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?auto=format&fit=crop&w=1000&q=85",
        "sku": "BAG-FORM-OLV",
        "size": "One size",
        "color": "Olive",
        "price": "49500.00",
        "quantity": 5,
        "featured": False,
    },
    {
        "category": "Accessories",
        "name": "Everyday Gold Hoops",
        "description": "Lightweight polished hoops that make an everyday outfit feel finished.",
        "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1000&q=85",
        "sku": "ACC-HOOP-GLD",
        "size": "One size",
        "color": "Gold",
        "price": "18500.00",
        "quantity": 15,
        "featured": False,
    },
]


class Command(BaseCommand):
    help = "Create sample saleable products and initial inventory for local development."

    def handle(self, *args, **options):
        for item in PRODUCTS:
            category_name = item["category"]
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": slugify(category_name)},
            )
            product_slug = slugify(item["name"])
            product, _ = Product.objects.update_or_create(
                slug=product_slug,
                defaults={
                    "category": category,
                    "name": item["name"],
                    "description": item["description"],
                    "image_url": item["image_url"],
                    "is_active": True,
                    "featured": item["featured"],
                },
            )
            variant, _ = Variant.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "product": product,
                    "size": item["size"],
                    "color": item["color"],
                    "price": Decimal(item["price"]),
                    "is_active": True,
                },
            )
            stock, _ = StockLevel.objects.get_or_create(
                variant=variant,
                defaults={"quantity": item["quantity"]},
            )
            if stock.quantity != item["quantity"]:
                delta = item["quantity"] - stock.quantity
                stock.quantity = item["quantity"]
                stock.save(update_fields=["quantity", "updated_at"])
                StockMovement.objects.create(
                    stock=stock,
                    delta=delta,
                    reason="Demo catalog seed",
                )

        self.stdout.write(self.style.SUCCESS("Sample fashion catalog is ready."))
