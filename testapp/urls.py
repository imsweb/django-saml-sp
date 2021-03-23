from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("sso/<idp_slug>/", include("sp.urls")),
    path("admin/", admin.site.urls),
]
