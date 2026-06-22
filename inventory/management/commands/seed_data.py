from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from inventory.models import Category, Product


class Command(BaseCommand):
    help = "Seed sample categories and products"

    def handle(self, *args, **options):
        # Clear existing data
        Product.objects.all().delete()
        Category.objects.all().delete()

        # Create categories
        electronics = Category.objects.create(name="Electronics", slug="electronics")
        clothing = Category.objects.create(name="Clothing", slug="clothing")
        books = Category.objects.create(name="Books", slug="books")

        # Create products
        products_data = [
            {
                "sku": "LAPTOP001",
                "name": "Pro Laptop 15",
                "description": "High-performance laptop with 15-inch display",
                "category": electronics,
                "stock_quantity": 25,
                "price": Decimal("1299.99"),
                "discount_price": Decimal("1099.99"),
                "is_on_sale": True,
                "sale_start_date": timezone.now(),
                "sale_end_date": timezone.now() + timezone.timedelta(days=30),
            },
            {
                "sku": "MOUSE001",
                "name": "Wireless Mouse",
                "description": "Ergonomic wireless mouse with 2.4GHz receiver",
                "category": electronics,
                "stock_quantity": 100,
                "price": Decimal("29.99"),
                "discount_price": None,
                "is_on_sale": False,
            },
            {
                "sku": "KEYBOARD001",
                "name": "Mechanical Keyboard",
                "description": "RGB mechanical keyboard with Cherry MX switches",
                "category": electronics,
                "stock_quantity": 50,
                "price": Decimal("149.99"),
                "discount_price": Decimal("119.99"),
                "is_on_sale": True,
                "sale_start_date": timezone.now(),
                "sale_end_date": timezone.now() + timezone.timedelta(days=14),
            },
            {
                "sku": "SHIRT001",
                "name": "Cotton T-Shirt",
                "description": "100% cotton comfortable t-shirt",
                "category": clothing,
                "stock_quantity": 200,
                "price": Decimal("19.99"),
                "discount_price": None,
                "is_on_sale": False,
            },
            {
                "sku": "JEANS001",
                "name": "Blue Jeans",
                "description": "Classic blue denim jeans",
                "category": clothing,
                "stock_quantity": 150,
                "price": Decimal("59.99"),
                "discount_price": Decimal("39.99"),
                "is_on_sale": True,
                "sale_start_date": timezone.now() - timezone.timedelta(days=5),
                "sale_end_date": timezone.now() + timezone.timedelta(days=10),
            },
            {
                "sku": "BOOK001",
                "name": "Django for Beginners",
                "description": "Learn Django web development from scratch",
                "category": books,
                "stock_quantity": 75,
                "price": Decimal("29.99"),
                "discount_price": None,
                "is_on_sale": False,
            },
            {
                "sku": "BOOK002",
                "name": "Python Mastery",
                "description": "Advanced Python programming techniques",
                "category": books,
                "stock_quantity": 60,
                "price": Decimal("39.99"),
                "discount_price": Decimal("24.99"),
                "is_on_sale": True,
                "sale_start_date": timezone.now(),
                "sale_end_date": timezone.now() + timezone.timedelta(days=7),
            },
            {
                "sku": "MONITOR001",
                "name": "4K Monitor 27",
                "description": "27-inch 4K UHD monitor with HDR support",
                "category": electronics,
                "stock_quantity": 30,
                "price": Decimal("499.99"),
                "discount_price": Decimal("399.99"),
                "is_on_sale": True,
                "sale_start_date": timezone.now() - timezone.timedelta(days=2),
                "sale_end_date": timezone.now() + timezone.timedelta(days=20),
            },
        ]

        for data in products_data:
            Product.objects.create(**data)

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Created {len(products_data)} products in {len([electronics, clothing, books])} categories"
            )
        )
