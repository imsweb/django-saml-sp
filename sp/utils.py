import datetime

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured

from .models import IdP

IDP_SESSION_KEY = "_idp_slug"


def authenticate(request, idp, saml):
    return auth.authenticate(request, idp=idp, saml=saml)


def login(request, user, idp, saml):
    auth.login(request, user)
    request.session[IDP_SESSION_KEY] = idp.slug
    if idp.respect_expiration:
        if not settings.SESSION_SERIALIZER.endswith("PickleSerializer"):
            raise ImproperlyConfigured(
                "IdP-based session expiration is only supported with the PickleSerializer SESSION_SERIALIZER."
            )
        try:
            dt = datetime.datetime.fromtimestamp(saml.get_session_expiration(), tz=datetime.timezone.utc)
            request.session.set_expiry(dt)
        except TypeError:
            pass


def get_session_idp(request):
    return IdP.objects.filter(slug=request.session.get(IDP_SESSION_KEY)).first()
