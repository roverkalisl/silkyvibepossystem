from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from inventory.views import HomePageView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("inventory.api_urls")),
    path("pages/", include("inventory.page_urls")),
]

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
