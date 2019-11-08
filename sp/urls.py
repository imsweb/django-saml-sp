from django.urls import path

from . import views

urlpatterns = [
    path("<idp_slug>/", views.metadata, name="sp-idp-metadata"),
    path("<idp_slug>/acs/", views.acs, name="sp-idp-acs"),
    path("<idp_slug>/login/", views.login, name="sp-idp-login"),
    path("<idp_slug>/test/", views.login, {"test": True}, name="sp-idp-test"),
    path("<idp_slug>/verify/", views.login, {"verify": True}, name="sp-idp-verify"),
]
