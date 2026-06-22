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


@admin.action(description="Mark selected orders as payment verified")
def verify_payment(modeladmin, request, queryset):
    updated = queryset.filter(payment_status=Order.PAYMENT_STATUS_PENDING).update(
        payment_status=Order.PAYMENT_STATUS_VERIFIED,
        status=Order.STATUS_PAID,
    )
    modeladmin.message_user(request, f"Marked {updated} orders as payment verified.")


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
    list_display = ("order_number", "status", "payment_method", "payment_status", "customer_name", "customer_email", "total_amount", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "customer_name", "customer_email")
    actions = (verify_payment,)
    inlines = (OrderItemInline,)


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("product", "change_amount", "note", "user", "created_at")
    search_fields = ("product__sku", "product__name", "note")
