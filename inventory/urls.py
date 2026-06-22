from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("orders/", views.OrderCreateView.as_view(), name="order-create"),
    path("special-offers/", views.SpecialOffersListView.as_view(), name="special-offers"),
    path("inventory/", views.InventoryListView.as_view(), name="inventory-list"),
    path("stock-update/", views.StockUpdateView.as_view(), name="stock-update"),
]
