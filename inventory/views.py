from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import secrets

from .forms import CategoryForm, ProductForm
from .models import Category, InventoryLog, Product, Order, OrderItem
from .serializers import OrderSerializer, ProductSerializer
from rest_framework.exceptions import ValidationError


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_products"] = Product.objects.order_by("name")[:6]
        context["special_offers_count"] = Product.objects.filter(
            is_on_sale=True,
            discount_price__isnull=False,
            sale_start_date__lte=timezone.now(),
            sale_end_date__gte=timezone.now(),
        ).count()
        return context


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
            order = Order.objects.create(
                order_number=order_number,
                customer_name=data.get("customer_name", ""),
                customer_email=data.get("customer_email", ""),
                status=Order.STATUS_PAID if payment_method else Order.STATUS_PENDING,
                payment_method=payment_method,
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
