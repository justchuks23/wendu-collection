from django.contrib import admin

from .models import Category, Product, Variant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    can_delete = False
    fields = ("sku", "size", "color", "price", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "featured", "updated_at")
    list_filter = ("category", "is_active", "featured")
    search_fields = ("name", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VariantInline]

    def has_delete_permission(self, request, obj=None):
        return False
