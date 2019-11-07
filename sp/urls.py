from django.urls import path

from . import views


urlpatterns = [
    path("metadata/<sp_slug>/", views.metadata, name="sp-metadata"),
    path("acs/<sp_slug>/", views.acs, name="sp-acs"),
    path("login/<sp_slug>/<idp_slug>/", views.login, name="sp-idp-login"),
    path("test/<sp_slug>/<idp_slug>/", views.login, {"test": True}, name="sp-idp-test"),
    path("verify/<sp_slug>/<idp_slug>/", views.login, {"verify": True}, name="sp-idp-verify"),
]
