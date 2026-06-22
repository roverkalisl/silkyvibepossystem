from django.urls import path
from .views import OrderCreateView, ProductDetailView, ProductListView, SpecialOffersListView, InventoryListView, StockUpdateView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("orders/", OrderCreateView.as_view(), name="order-create"),
    path("special-offers/", SpecialOffersListView.as_view(), name="special-offers"),
    path("inventory/", InventoryListView.as_view(), name="inventory-list"),
    path("stock-update/", StockUpdateView.as_view(), name="stock-update"),
]
