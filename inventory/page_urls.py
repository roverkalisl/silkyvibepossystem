from django.urls import path
from .views import (
    CategoryCreatePageView,
    CategoryListPageView,
    HomePageView,
    ProductCreatePageView,
    ProductDetailPageView,
    ProductListPageView,
    SpecialOffersPageView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home-page"),
    path("products/", ProductListPageView.as_view(), name="product-list-page"),
    path("products/add/", ProductCreatePageView.as_view(), name="product-add-page"),
    path("products/<int:pk>/", ProductDetailPageView.as_view(), name="product-detail-page"),
    path("special-offers/", SpecialOffersPageView.as_view(), name="special-offers-page"),
    path("categories/", CategoryListPageView.as_view(), name="category-list-page"),
    path("categories/add/", CategoryCreatePageView.as_view(), name="category-add-page"),
]
