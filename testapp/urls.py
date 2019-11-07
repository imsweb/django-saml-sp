from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("sso/", include("sp.urls")),
    path("admin/", admin.site.urls),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
]
