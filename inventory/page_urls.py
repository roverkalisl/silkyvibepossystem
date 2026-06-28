from django.urls import path
from .views import (
    CategoryCreatePageView,
    CategoryListPageView,
    DashboardPageView,
    HomePageView,
    ProductCreatePageView,
    ProductDetailPageView,
    ProductListPageView,
    SpecialOffersPageView,
    POSCheckoutPageView,
    CartPageView,
    CheckoutPageView,
    AdminLoginPageView,
    CustomerLoginPageView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home-page"),
    path("dashboard/", DashboardPageView.as_view(), name="dashboard-page"),
    path("products/", ProductListPageView.as_view(), name="product-list-page"),
    path("products/add/", ProductCreatePageView.as_view(), name="product-add-page"),
    path("products/<int:pk>/", ProductDetailPageView.as_view(), name="product-detail-page"),
    path("special-offers/", SpecialOffersPageView.as_view(), name="special-offers-page"),
    path("pos/checkout/", POSCheckoutPageView.as_view(), name="pos-checkout-page"),
    path("cart/", CartPageView.as_view(), name="cart-page"),
    path("checkout/", CheckoutPageView.as_view(), name="checkout-page"),
    path("admin-login/", AdminLoginPageView.as_view(), name="admin-login-page"),
    path("customer-login/", CustomerLoginPageView.as_view(), name="customer-login-page"),
    path("categories/", CategoryListPageView.as_view(), name="category-list-page"),
    path("categories/add/", CategoryCreatePageView.as_view(), name="category-add-page"),
]
