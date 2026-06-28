import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Order, Product, ProductColor, ProductSize


class OnlineOrderFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Footwear", slug="footwear")
        brand = Brand.objects.create(name="Trend", slug="trend")
        size = ProductSize.objects.create(label="M")
        color = ProductColor.objects.create(name="Black", hex_code="#000000")
        self.product = Product.objects.create(
            sku="SKU-100",
            barcode="1001",
            name="Running Shoes",
            description="Comfortable shoes",
            category=category,
            brand=brand,
            size=size,
            color=color,
            stock_quantity=5,
            price=Decimal("1200.00"),
            discount_price=Decimal("999.00"),
            is_on_sale=True,
            sale_start_date="2024-01-01T00:00:00Z",
            sale_end_date="2030-01-01T00:00:00Z",
        )

    def test_cash_online_order_is_kept_pending_for_verification(self):
        payload = {
            "customer_name": "Asha Perera",
            "customer_email": "asha@example.com",
            "payment_method": "cash",
            "items": [{"product_id": self.product.id, "quantity": 2}],
        }

        response = self.client.post(
            reverse("online-order-create"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        order = Order.objects.get(order_number=data["order_number"])
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PENDING)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
