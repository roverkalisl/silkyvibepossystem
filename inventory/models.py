from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "brands"

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    label = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.label


class ProductColor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hex_code = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL, related_name="warehouses")
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    loyalty_points = models.IntegerField(default=0)
    lifetime_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def award_loyalty_points(self, amount):
        points = int(amount // 100)
        self.loyalty_points = F("loyalty_points") + points
        self.lifetime_value = F("lifetime_value") + Decimal(amount)
        self.save(update_fields=["loyalty_points", "lifetime_value"])


class Coupon(models.Model):
    DISCOUNT_TYPE_PERCENTAGE = "percentage"
    DISCOUNT_TYPE_FIXED = "fixed"

    DISCOUNT_CHOICES = [
        (DISCOUNT_TYPE_PERCENTAGE, "Percentage"),
        (DISCOUNT_TYPE_FIXED, "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default=DISCOUNT_TYPE_PERCENTAGE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    minimum_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    @property
    def is_active(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def apply_discount(self, total_amount):
        if total_amount is None:
            return Decimal(0)
        amount = Decimal(total_amount)
        if self.discount_type == self.DISCOUNT_TYPE_PERCENTAGE:
            discount = (amount * self.discount_amount) / Decimal(100)
        else:
            discount = self.discount_amount
        final = amount - discount
        return final if final >= 0 else Decimal(0)


class DeliveryPartner(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    size = models.ForeignKey(ProductSize, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    color = models.ForeignKey(ProductColor, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    stock_quantity = models.IntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    damaged_quantity = models.PositiveIntegerField(default=0)
    returned_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=5)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_on_sale = models.BooleanField(default=False)
    sale_start_date = models.DateTimeField(null=True, blank=True)
    sale_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["is_on_sale", "sale_start_date", "sale_end_date"]),
        ]

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        now = timezone.now()
        if self.is_on_sale and self.discount_price is not None and self.sale_start_date and self.sale_end_date:
            if self.sale_start_date <= now <= self.sale_end_date:
                return self.discount_price
        return self.price

    @property
    def sale_percentage(self):
        if self.final_price < self.price and self.price > 0:
            return int(((self.price - self.final_price) / self.price) * 100)
        return 0

    @property
    def available_stock(self):
        return self.stock_quantity - self.reserved_quantity

    @property
    def current_stock(self):
        return self.stock_quantity

    @property
    def is_low_stock(self):
        return self.available_stock <= self.min_stock_level

    def decrease_stock(self, quantity):
        if quantity <= 0:
            return
        outcome = Product.objects.filter(pk=self.pk, stock_quantity__gte=quantity).update(
            stock_quantity=F("stock_quantity") - quantity
        )
        if outcome == 0:
            raise ValueError("Insufficient stock for product: {}".format(self.sku))
        self.refresh_from_db()

    def increase_stock(self, quantity):
        if quantity <= 0:
            return
        Product.objects.filter(pk=self.pk).update(stock_quantity=F("stock_quantity") + quantity)
        self.refresh_from_db()

    def reserve_stock(self, quantity):
        if quantity <= 0:
            return
        outcome = Product.objects.filter(pk=self.pk, stock_quantity__gte=F("reserved_quantity") + quantity).update(
            reserved_quantity=F("reserved_quantity") + quantity
        )
        if outcome == 0:
            raise ValueError("Insufficient available stock to reserve for product: {}".format(self.sku))
        self.refresh_from_db()

    def release_reserved_stock(self, quantity):
        if quantity <= 0:
            return
        outcome = Product.objects.filter(pk=self.pk, reserved_quantity__gte=quantity).update(
            reserved_quantity=F("reserved_quantity") - quantity
        )
        if outcome == 0:
            raise ValueError("Cannot release {} reserved units for product: {}".format(quantity, self.sku))
        self.refresh_from_db()

    def mark_damaged(self, quantity):
        if quantity <= 0:
            return
        outcome = Product.objects.filter(pk=self.pk, stock_quantity__gte=quantity).update(
            stock_quantity=F("stock_quantity") - quantity,
            damaged_quantity=F("damaged_quantity") + quantity,
        )
        if outcome == 0:
            raise ValueError("Insufficient stock to mark damaged for product: {}".format(self.sku))
        self.refresh_from_db()

    def receive_return(self, quantity):
        if quantity <= 0:
            return
        Product.objects.filter(pk=self.pk).update(
            stock_quantity=F("stock_quantity") + quantity,
            returned_quantity=F("returned_quantity") + quantity,
        )
        self.refresh_from_db()


class ProductImage(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.product.name} image {self.sort_order}"


class BankAccount(models.Model):
    bank_name = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=100, blank=True)
    branch_name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=100, blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Nepal")
    phone_number = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.label or self.city}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} -> {self.new_status}"


class ReturnRequest(models.Model):
    TYPE_RETURN = "return"
    TYPE_EXCHANGE = "exchange"
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_COMPLETED = "completed"

    TYPE_CHOICES = [
        (TYPE_RETURN, "Return"),
        (TYPE_EXCHANGE, "Exchange"),
    ]
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_COMPLETED, "Completed"),
    ]

    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="return_requests")
    order_item = models.ForeignKey("OrderItem", null=True, blank=True, on_delete=models.SET_NULL)
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_RETURN)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    quantity = models.PositiveIntegerField(default=1)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.get_request_type_display()}"


class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_items")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="warehouse_stock")
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("warehouse", "product")

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAID, "Paid"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_CASH = "cash"
    PAYMENT_CARD = "card"
    PAYMENT_BANK_DEPOSIT = "bank_deposit"
    PAYMENT_COD = "cod"
    PAYMENT_MIXED = "mixed"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_CARD, "Card"),
        (PAYMENT_BANK_DEPOSIT, "Bank Deposit"),
        (PAYMENT_COD, "Cash on Delivery"),
        (PAYMENT_MIXED, "Mixed Payment"),
    ]

    PAYMENT_STATUS_PENDING = "pending"
    PAYMENT_STATUS_VERIFIED = "verified"
    PAYMENT_STATUS_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_VERIFIED, "Verified"),
        (PAYMENT_STATUS_FAILED, "Failed"),
    ]

    DELIVERY_PENDING = "pending"
    DELIVERY_CONFIRMED = "confirmed"
    DELIVERY_PACKED = "packed"
    DELIVERY_SHIPPED = "shipped"
    DELIVERY_DELIVERED = "delivered"
    DELIVERY_CANCELLED = "cancelled"

    DELIVERY_STATUS_CHOICES = [
        (DELIVERY_PENDING, "Pending"),
        (DELIVERY_CONFIRMED, "Confirmed"),
        (DELIVERY_PACKED, "Packed"),
        (DELIVERY_SHIPPED, "Shipped"),
        (DELIVERY_DELIVERED, "Delivered"),
        (DELIVERY_CANCELLED, "Cancelled"),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    order_type = models.CharField(
        max_length=20,
        choices=[
            ("pos", "POS"),
            ("online", "Online"),
        ],
        default="online",
    )
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    customer_address = models.ForeignKey(
        "CustomerAddress",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    delivery_partner = models.ForeignKey(DeliveryPartner, null=True, blank=True, on_delete=models.SET_NULL)
    tracking_number = models.CharField(max_length=100, blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default=DELIVERY_PENDING)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_method = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_CASH)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_VERIFIED)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_slip = models.FileField(upload_to="payment_slips/", blank=True, null=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

    def calculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        if self.coupon and self.coupon.is_active:
            total = self.coupon.apply_discount(total)
        total += self.delivery_charge
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount}"


class PurchaseOrder(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ORDERED = "ordered"
    STATUS_PARTIAL = "partial"
    STATUS_RECEIVED = "received"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ORDERED, "Ordered"),
        (STATUS_PARTIAL, "Partially Received"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expected_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

    def calculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        self.total_cost = total
        self.save(update_fields=["total_cost"])
        return total

    def receive_stock(self, received_items):
        for item_data in received_items:
            item = self.items.filter(pk=item_data.get("id")).first()
            if not item:
                continue
            receive_qty = min(item.quantity_ordered - item.quantity_received, int(item_data.get("quantity", 0)))
            if receive_qty <= 0:
                continue
            item.quantity_received += receive_qty
            item.save(update_fields=["quantity_received"])
            item.product.increase_stock(receive_qty)
            InventoryLog.objects.create(
                product=item.product,
                change_amount=receive_qty,
                note=f"Received from PO {self.order_number}",
            )
        if self.items.filter(quantity_received__lt=models.F("quantity_ordered")).exists():
            self.status = self.STATUS_PARTIAL
        else:
            self.status = self.STATUS_RECEIVED
        self.save(update_fields=["status"])


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def line_total(self):
        return self.quantity_ordered * self.cost_price


class InventoryLog(models.Model):
    TRANSACTION_SALE = "sale"
    TRANSACTION_PURCHASE = "purchase"
    TRANSACTION_ADJUSTMENT = "adjustment"
    TRANSACTION_RETURN = "return"
    TRANSACTION_DAMAGE = "damage"
    TRANSACTION_RESERVE = "reserve"
    TRANSACTION_RELEASE = "release"

    TRANSACTION_CHOICES = [
        (TRANSACTION_SALE, "Sale"),
        (TRANSACTION_PURCHASE, "Purchase"),
        (TRANSACTION_ADJUSTMENT, "Adjustment"),
        (TRANSACTION_RETURN, "Return"),
        (TRANSACTION_DAMAGE, "Damage"),
        (TRANSACTION_RESERVE, "Reserve"),
        (TRANSACTION_RELEASE, "Release"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_logs")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES, default=TRANSACTION_ADJUSTMENT)
    change_amount = models.IntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.sku} {self.transaction_type} {self.change_amount}"


class StaffProfile(models.Model):
    ROLE_SUPER_ADMIN = "super_admin"
    ROLE_MANAGER = "manager"
    ROLE_CASHIER = "cashier"
    ROLE_STORE_KEEPER = "store_keeper"
    ROLE_ONLINE_ORDER_STAFF = "online_order_staff"

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, "Super Admin"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_CASHIER, "Cashier"),
        (ROLE_STORE_KEEPER, "Store Keeper"),
        (ROLE_ONLINE_ORDER_STAFF, "Online Order Staff"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_CASHIER)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
