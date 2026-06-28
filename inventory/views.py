from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum, DecimalField
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import secrets
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from .forms import CategoryForm, ProductForm
from .models import (
    Category,
    Coupon,
    Customer,
    DeliveryPartner,
    Expense,
    ExpenseCategory,
    InventoryLog,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    Order,
    OrderItem,
)
from .serializers import (
    CouponSerializer,
    CustomerSerializer,
    DeliveryPartnerSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    OrderSerializer,
    ProductSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)
from rest_framework.exceptions import ValidationError


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context["featured_products"] = Product.objects.order_by("name")[:6]
        context["categories"] = Category.objects.order_by("name")[:8]
        context["special_offers_count"] = Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=now,
            sale_end_date__gte=now,
        ).count()
        context["sale_products"] = Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=now,
            sale_end_date__gte=now,
        ).order_by("-updated_at")[:4]
        return context


class DashboardPageView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = now.date()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year = now.year
        current_month = now.month

        today_orders = Order.objects.filter(created_at__date=today)
        today_sales = today_orders.filter(status__in=[Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED])
        monthly_revenue = Order.objects.filter(created_at__gte=current_month_start).aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        monthly_expenses = Expense.objects.filter(expense_date__month=current_month, expense_date__year=current_year).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        context["pos_orders_count"] = Order.objects.filter(order_number__startswith="POS-").count()
        context["online_orders_count"] = Order.objects.exclude(order_number__startswith="POS-").count()
        context["products_count"] = Product.objects.count()
        context["low_stock_count"] = Product.objects.filter(stock_quantity__lte=F("min_stock_level")).count()
        context["pending_orders_count"] = Order.objects.filter(status=Order.STATUS_PENDING).count()
        context["payment_verification_count"] = Order.objects.filter(payment_status=Order.PAYMENT_STATUS_PENDING).count()
        context["total_customers_count"] = Customer.objects.count()
        context["today_sales_count"] = today_sales.count()
        context["today_sales_total"] = today_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        context["monthly_revenue"] = monthly_revenue
        context["monthly_expenses"] = monthly_expenses
        context["net_profit"] = monthly_revenue - monthly_expenses
        context["special_offers_count"] = Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=now,
            sale_end_date__gte=now,
        ).count()
        context["best_selling_products"] = (
            OrderItem.objects.values("product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )
        context["recent_orders"] = Order.objects.order_by("-created_at")[:6]
        context["recent_low_stock_products"] = Product.objects.filter(stock_quantity__lte=F("min_stock_level")).order_by("stock_quantity")[:6]
        return context


class AdminLoginPageView(FormView):
    template_name = "admin_login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "You must be an admin/staff user to sign in here.")
            return self.form_invalid(form)
        login(self.request, user)
        return redirect("admin:index")


class CustomerLoginPageView(FormView):
    template_name = "customer_login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        next_url = self.request.GET.get("next") or "/"
        return redirect(next_url)


class ProductListPageView(ListView):
    model = Product
    template_name = "product_list.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        on_sale = self.request.GET.get("on_sale")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if category:
            queryset = queryset.filter(category__slug=category)
        if on_sale == "true":
            now = timezone.now()
            queryset = queryset.filter(
                is_on_sale=True,
                discount_price__isnull=False,
                sale_start_date__lte=now,
                sale_end_date__gte=now,
            )
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset


class ProductDetailPageView(DetailView):
    model = Product
    template_name = "product_detail.html"
    context_object_name = "product"


class SpecialOffersPageView(ListView):
    model = Product
    template_name = "special_offers.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        now = timezone.now()
        return Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=now,
            sale_end_date__gte=now,
        )


class CategoryCreatePageView(FormView):
    template_name = "category_create.html"
    form_class = CategoryForm

    def form_valid(self, form):
        form.save()
        return redirect(reverse("category-list-page"))


class CategoryListPageView(ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = "categories"


class ProductCreatePageView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_create.html"

    def get_success_url(self):
        return reverse("product-list-page")


class SpecialOffersListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        now = timezone.now()
        return Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=now,
            sale_end_date__gte=now,
        )


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        on_sale = self.request.query_params.get("on_sale")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if category:
            queryset = queryset.filter(category__slug=category)
        if on_sale == "true":
            now = timezone.now()
            queryset = queryset.filter(
                is_on_sale=True,
                discount_price__isnull=False,
                sale_start_date__lte=now,
                sale_end_date__gte=now,
            )
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]


class LowStockListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Product.objects.annotate(
            available_stock=F("stock_quantity") - F("reserved_quantity")
        ).filter(available_stock__lte=F("min_stock_level"))


class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAdminUser]


class SupplierDetailView(generics.RetrieveAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAdminUser]


class CustomerListView(generics.ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAdminUser]


class CustomerDetailView(generics.RetrieveAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAdminUser]


class DeliveryPartnerListCreateView(generics.ListCreateAPIView):
    queryset = DeliveryPartner.objects.all()
    serializer_class = DeliveryPartnerSerializer
    permission_classes = [permissions.IsAdminUser]


class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class ExpenseCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAdminUser]


class ExpenseListCreateView(generics.ListCreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAdminUser]


class PurchaseOrderListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAdminUser]


class PurchaseOrderDetailView(generics.RetrieveAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAdminUser]


class PurchaseOrderReceiveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        items = request.data.get("items", [])

        try:
            purchase_order = PurchaseOrder.objects.select_for_update().get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({"detail": "Purchase order not found."}, status=status.HTTP_404_NOT_FOUND)

        purchase_order.receive_stock(items)
        return Response(
            {
                "order_number": purchase_order.order_number,
                "status": purchase_order.status,
                "total_cost": purchase_order.total_cost,
            }
        )


class ReportSummaryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        sales_total = Order.objects.filter(payment_status=Order.PAYMENT_STATUS_VERIFIED).aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        cogs_total = OrderItem.objects.aggregate(
            cogs=Sum(
                F("quantity") * F("product__cost_price"),
                output_field=DecimalField(max_digits=16, decimal_places=2),
            )
        )["cogs"] or Decimal("0")

        expenses_total = Expense.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        purchases_total = PurchaseOrder.objects.aggregate(total=Sum("total_cost"))["total"] or Decimal("0")

        low_stock_count = Product.objects.annotate(
            available_stock=F("stock_quantity") - F("reserved_quantity")
        ).filter(available_stock__lte=F("min_stock_level")).count()

        top_selling = (
            OrderItem.objects.values("product__id", "product__name")
            .annotate(quantity_sold=Sum("quantity"))
            .order_by("-quantity_sold")[:5]
        )

        return Response(
            {
                "sales_total": sales_total,
                "cogs_total": cogs_total,
                "expenses_total": expenses_total,
                "purchases_total": purchases_total,
                "net_profit": sales_total - cogs_total - expenses_total,
                "low_stock_count": low_stock_count,
                "top_selling_products": list(top_selling),
            }
        )


class InventoryListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]


class StockUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request):
        sku = request.data.get("sku")
        quantity = request.data.get("quantity")
        note = request.data.get("note", "Stock update")

        if sku is None or quantity is None:
            return Response({"detail": "sku and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"detail": "quantity must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.select_for_update().get(sku=sku)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        product.stock_quantity = F("stock_quantity") + quantity
        product.save(update_fields=["stock_quantity"])
        product.refresh_from_db()
        InventoryLog.objects.create(product=product, change_amount=quantity, note=note, user=request.user if request.user.is_authenticated else None)

        return Response({"sku": product.sku, "stock_quantity": product.stock_quantity})


class ProductBySKUView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "sku"


class POSOrderCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        data = request.data
        cashier_name = data.get("cashier_name", "")
        register_id = data.get("register_id", "")
        payment_method = data.get("payment_method", "")
        items = data.get("items", [])

        if not items:
            return Response({"detail": "Order must include at least one item."}, status=status.HTTP_400_BAD_REQUEST)

        # Collect SKUs and quantities
        skus = [item.get("sku") for item in items]
        if None in skus:
            return Response({"detail": "Each item must include a sku."}, status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.select_for_update().filter(sku__in=skus)
        products_by_sku = {p.sku: p for p in products}

        # generate a unique POS order number
        order_number = f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"

        # create order record
        order = None
        try:
            # Set payment_status based on payment method
            if payment_method in [Order.PAYMENT_COD, Order.PAYMENT_BANK_DEPOSIT, Order.PAYMENT_CASH]:
                payment_status = Order.PAYMENT_STATUS_PENDING
                order_status = Order.STATUS_PENDING
            else:
                payment_status = Order.PAYMENT_STATUS_VERIFIED
                order_status = Order.STATUS_PAID

            order = Order.objects.create(
                order_number=order_number,
                customer_name=data.get("customer_name", ""),
                customer_email=data.get("customer_email", ""),
                status=order_status,
                payment_method=payment_method,
                payment_status=payment_status,
            )

            total = 0
            for item in items:
                sku = item.get("sku")
                quantity = int(item.get("quantity", 0))
                product = products_by_sku.get(sku)
                if not product:
                    raise ValidationError(f"Product with sku {sku} not found.")
                if product.stock_quantity < quantity:
                    raise ValidationError(f"Insufficient stock for {product.name}.")
                product.decrease_stock(quantity)
                unit_price = product.final_price
                OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=unit_price)
                total += unit_price * quantity

            order.total_amount = total
            order.save(update_fields=["total_amount"])
        except Exception as exc:
            if order is not None:
                order.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"order_number": order.order_number, "total_amount": order.total_amount})


class POSCheckoutPageView(TemplateView):
    template_name = "pos_checkout.html"


class CartPageView(TemplateView):
    template_name = "shopping_cart.html"


class CheckoutPageView(TemplateView):
    template_name = "checkout.html"


class OnlineOrderCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        data = request.data
        customer_name = data.get("customer_name", "")
        customer_email = data.get("customer_email", "")
        payment_method = data.get("payment_method", "")
        items = data.get("items", [])

        if not items:
            return Response({"detail": "Order must include at least one item."}, status=status.HTTP_400_BAD_REQUEST)

        # Collect product IDs and quantities
        product_ids = [item.get("product_id") for item in items]
        if None in product_ids:
            return Response({"detail": "Each item must include a product_id."}, status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_by_id = {p.id: p for p in products}

        # Generate order number
        order_number = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"

        # Create order
        order = None
        try:
            # Set payment_status based on payment method
            if payment_method in [Order.PAYMENT_COD, Order.PAYMENT_BANK_DEPOSIT, Order.PAYMENT_CASH]:
                payment_status = Order.PAYMENT_STATUS_PENDING
                order_status = Order.STATUS_PENDING
            else:
                payment_status = Order.PAYMENT_STATUS_VERIFIED
                order_status = Order.STATUS_PAID

            order = Order.objects.create(
                order_number=order_number,
                customer_name=customer_name,
                customer_email=customer_email,
                status=order_status,
                payment_method=payment_method,
                payment_status=payment_status,
            )

            total = 0
            for item in items:
                product_id = item.get("product_id")
                quantity = int(item.get("quantity", 0))
                product = products_by_id.get(product_id)
                if not product:
                    raise ValidationError(f"Product with id {product_id} not found.")
                if product.stock_quantity < quantity:
                    raise ValidationError(f"Insufficient stock for {product.name}.")
                product.decrease_stock(quantity)
                product.refresh_from_db()
                unit_price = product.final_price
                OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=unit_price)
                total += unit_price * quantity

            order.total_amount = total
            order.save(update_fields=["total_amount"])
        except Exception as exc:
            if order is not None:
                order.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"order_number": order.order_number, "total_amount": order.total_amount, "status": "success"})
