from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Category,
    Coupon,
    Customer,
    DeliveryPartner,
    Expense,
    ExpenseCategory,
    Order,
    OrderItem,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "loyalty_points",
            "lifetime_value",
            "outstanding_balance",
            "created_at",
        )
        read_only_fields = ("loyalty_points", "lifetime_value", "outstanding_balance", "created_at")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "address",
            "balance",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class CouponSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "discount_type",
            "discount_amount",
            "usage_limit",
            "used_count",
            "minimum_order_value",
            "active",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("used_count", "is_active", "created_at", "updated_at")


class DeliveryPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPartner
        fields = ("id", "name", "phone", "email", "address")


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ("id", "name")


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = (
            "id",
            "category",
            "description",
            "amount",
            "expense_date",
            "created_by",
            "created_at",
        )
        read_only_fields = ("created_at",)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = PurchaseOrderItem
        fields = (
            "id",
            "product",
            "quantity_ordered",
            "quantity_received",
            "cost_price",
        )
        read_only_fields = ("quantity_received",)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "supplier",
            "order_number",
            "status",
            "total_cost",
            "expected_delivery_date",
            "notes",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("total_cost", "created_at", "updated_at")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Purchase order must contain at least one item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        total = Decimal(0)
        for item_data in items_data:
            item = PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=item_data["product"],
                quantity_ordered=item_data["quantity_ordered"],
                cost_price=item_data["cost_price"],
            )
            total += item.line_total

        purchase_order.total_cost = total
        purchase_order.save(update_fields=["total_cost"])
        return purchase_order


class ProductSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sale_percentage = serializers.IntegerField(read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "barcode",
            "name",
            "description",
            "category",
            "brand",
            "size",
            "color",
            "image",
            "stock_quantity",
            "reserved_quantity",
            "available_stock",
            "damaged_quantity",
            "returned_quantity",
            "min_stock_level",
            "cost_price",
            "price",
            "discount_price",
            "is_on_sale",
            "sale_start_date",
            "sale_end_date",
            "final_price",
            "sale_percentage",
            "is_low_stock",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ("product", "quantity", "unit_price")
        read_only_fields = ("unit_price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False, allow_null=True)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    coupon = CouponSerializer(read_only=True)
    delivery_partner = serializers.PrimaryKeyRelatedField(queryset=DeliveryPartner.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "customer",
            "customer_name",
            "customer_email",
            "coupon",
            "coupon_code",
            "delivery_partner",
            "tracking_number",
            "delivery_status",
            "delivery_charge",
            "status",
            "payment_method",
            "payment_reference",
            "payment_status",
            "total_amount",
            "items",
            "created_at",
        )
        read_only_fields = ("total_amount", "created_at", "coupon")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must include at least one item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        coupon_code = validated_data.pop("coupon_code", None)
        customer = validated_data.pop("customer", None)
        customer_email = validated_data.get("customer_email", "")
        customer_name = validated_data.get("customer_name", "")

        if customer is None and customer_email:
            customer, _ = Customer.objects.get_or_create(
                email=customer_email,
                defaults={"name": customer_name or customer_email},
            )

        if customer is not None:
            validated_data["customer"] = customer

        coupon = None
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if not coupon or not coupon.is_active:
                raise serializers.ValidationError("Coupon code is invalid or inactive.")
            validated_data["coupon"] = coupon

        product_ids = [item["product"].id for item in items_data]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_by_id = {product.id: product for product in products}

        payment_method = validated_data.get("payment_method", "")
        if payment_method in [Order.PAYMENT_COD, Order.PAYMENT_BANK_DEPOSIT, Order.PAYMENT_CASH]:
            validated_data["payment_status"] = Order.PAYMENT_STATUS_PENDING
            validated_data["status"] = Order.STATUS_PENDING
        else:
            validated_data["payment_status"] = Order.PAYMENT_STATUS_VERIFIED
            validated_data["status"] = Order.STATUS_PAID

        order = Order.objects.create(**validated_data)
        total = Decimal(0)

        for item_data in items_data:
            product = products_by_id.get(item_data["product"].id)
            if not product:
                raise serializers.ValidationError("Product not found.")
            if product.stock_quantity < item_data["quantity"]:
                raise serializers.ValidationError(f"Insufficient stock for {product.name}.")
            product.decrease_stock(item_data["quantity"])
            unit_price = product.final_price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data["quantity"],
                unit_price=unit_price,
            )
            total += unit_price * item_data["quantity"]

        if coupon is not None:
            total = coupon.apply_discount(total)
            coupon.used_count = F("used_count") + 1
            coupon.save(update_fields=["used_count"])
            coupon.refresh_from_db()

        total += validated_data.get("delivery_charge", Decimal(0))
        order.total_amount = total
        order.save(update_fields=["total_amount"])

        if customer is not None:
            customer.award_loyalty_points(total)

        return order
