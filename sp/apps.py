from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SPConfig(AppConfig):
    name = "sp"
    verbose_name = _("SAML SP")
