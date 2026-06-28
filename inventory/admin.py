from decimal import Decimal

from django.contrib import admin
from .models import (
    Category,
    Coupon,
    Customer,
    DeliveryPartner,
    Expense,
    ExpenseCategory,
    InventoryLog,
    Order,
    OrderItem,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    StaffProfile,
    Supplier,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "balance", "created_at")
    search_fields = ("name", "email", "phone")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "loyalty_points", "lifetime_value", "outstanding_balance")
    search_fields = ("name", "email", "phone")


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_amount", "active", "starts_at", "ends_at")
    list_filter = ("discount_type", "active")
    search_fields = ("code",)


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "amount", "expense_date", "created_by", "created_at")
    list_filter = ("category", "expense_date")
    search_fields = ("description",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "stock_quantity",
        "available_stock",
        "min_stock_level",
        "price",
        "final_price",
        "is_on_sale",
        "is_low_stock",
    )
    list_filter = ("category", "is_on_sale")
    search_fields = ("sku", "name", "description")
    actions = ("enable_sale", "disable_sale", "apply_ten_percent_discount")
    readonly_fields = ("created_at", "updated_at")

    def enable_sale(self, request, queryset):
        queryset.update(is_on_sale=True)

    def disable_sale(self, request, queryset):
        queryset.update(is_on_sale=False)

    def apply_ten_percent_discount(self, request, queryset):
        for product in queryset:
            if product.price:
                product.discount_price = product.price * Decimal("0.9")
                product.save()

    enable_sale.short_description = "Enable sale for selected products"
    disable_sale.short_description = "Disable sale for selected products"
    apply_ten_percent_discount.short_description = "Apply 10% discount to selected products"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price",)


@admin.action(description="Mark selected orders as payment verified")
def verify_payment(modeladmin, request, queryset):
    updated = queryset.filter(payment_status=Order.PAYMENT_STATUS_PENDING).update(
        payment_status=Order.PAYMENT_STATUS_VERIFIED,
        status=Order.STATUS_PAID,
    )
    modeladmin.message_user(request, f"Marked {updated} orders as payment verified.")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "payment_method", "payment_status", "customer_name", "customer_email", "total_amount", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "customer_name", "customer_email")
    actions = (verify_payment,)
    inlines = (OrderItemInline,)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "supplier", "status", "total_cost", "expected_delivery_date", "created_at")
    list_filter = ("status", "expected_delivery_date")
    search_fields = ("order_number", "supplier__name")
    inlines = (PurchaseOrderItemInline,)


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "product", "quantity_ordered", "quantity_received", "cost_price")
    search_fields = ("purchase_order__order_number", "product__sku", "product__name")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("product", "transaction_type", "change_amount", "note", "user", "created_at")
    search_fields = ("product__sku", "product__name", "note")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
