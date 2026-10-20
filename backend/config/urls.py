from django.contrib import admin
from django.urls import include, path
from reportes.views import verify_report

urlpatterns = [
    path("verificar/<str:token>/", verify_report, name="verify-report"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("api.urls")),
]
