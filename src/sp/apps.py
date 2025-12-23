from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SPConfig(AppConfig):
    name = "sp"
    verbose_name = _("SAML SP")
    default_auto_field = "django.db.models.AutoField"
