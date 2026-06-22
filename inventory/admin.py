from django.contrib import admin
from .models import Category, InventoryLog, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.action(description="Enable sale for selected products")
def enable_sale(modeladmin, request, queryset):
    queryset.update(is_on_sale=True)


@admin.action(description="Disable sale for selected products")
def disable_sale(modeladmin, request, queryset):
    queryset.update(is_on_sale=False)


@admin.action(description="Apply 10% discount to selected products")
def apply_ten_percent_discount(modeladmin, request, queryset):
    for product in queryset:
        if product.price:
            product.discount_price = product.price * 0.9
            product.save()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "stock_quantity",
        "price",
        "final_price",
        "is_on_sale",
    )
    list_filter = ("category", "is_on_sale")
    search_fields = ("sku", "name", "description")
    actions = (enable_sale, disable_sale, apply_ten_percent_discount)
    readonly_fields = ("created_at", "updated_at")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "customer_name", "customer_email", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "customer_name", "customer_email")
    inlines = (OrderItemInline,)


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("product", "change_amount", "note", "user", "created_at")
    search_fields = ("product__sku", "product__name", "note")
