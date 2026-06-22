from django.db import transaction
from rest_framework import serializers
from .models import Category, Order, OrderItem, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sale_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "description",
            "category",
            "image",
            "stock_quantity",
            "price",
            "discount_price",
            "is_on_sale",
            "sale_start_date",
            "sale_end_date",
            "final_price",
            "sale_percentage",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ("product", "quantity", "unit_price")
        read_only_fields = ("unit_price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "customer_name",
            "customer_email",
            "status",
            "payment_method",
            "total_amount",
            "items",
            "created_at",
        )
        read_only_fields = ("total_amount", "created_at")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must include at least one item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        product_ids = [item["product"].id for item in items_data]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_by_id = {product.id: product for product in products}

        # Set payment_status based on payment_method
        payment_method = validated_data.get("payment_method", "")
        if payment_method in [Order.PAYMENT_COD, Order.PAYMENT_BANK_DEPOSIT]:
            validated_data["payment_status"] = Order.PAYMENT_STATUS_PENDING
        else:
            validated_data["payment_status"] = Order.PAYMENT_STATUS_VERIFIED

        order = Order.objects.create(**validated_data)
        total = 0

        for item_data in items_data:
            product = products_by_id.get(item_data["product"].id)
            if not product:
                raise serializers.ValidationError("Product not found.")
            if product.stock_quantity < item_data["quantity"]:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}."
                )
            product.decrease_stock(item_data["quantity"])
            unit_price = product.final_price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data["quantity"],
                unit_price=unit_price,
            )
            total += unit_price * item_data["quantity"]

        order.total_amount = total
        order.save(update_fields=["total_amount"])
        return order
