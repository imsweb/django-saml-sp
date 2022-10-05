import datetime

import django
from django.conf import settings
from django.contrib import auth
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string

from .models import IdP

IDP_SESSION_KEY = "_idpid"
NAMEID_SESSION_KEY = "_nameid"


def authenticate(request, idp, saml):
    return auth.authenticate(request, idp=idp, saml=saml)


def login(request, user, idp, saml):
    auth.login(request, user)
    # Store the authenticating IdP and actual (not mapped) SAML nameid in the session.
    set_session_idp(request, idp, saml.get_nameid())
    if idp.respect_expiration:
        if (
            django.VERSION[:2] < (4, 1)
            and settings.SESSION_SERIALIZER
            == "django.contrib.sessions.serializers.JSONSerializer"
        ):
            raise ImproperlyConfigured(
                "IdP-based session expiration is not supported using the "
                "JSONSerializer SESSION_SERIALIZER when using Django < 4.1."
            )
        try:
            dt = datetime.datetime.fromtimestamp(
                saml.get_session_expiration(), tz=datetime.timezone.utc
            )
            request.session.set_expiry(dt)
        except TypeError:
            pass


def logout(request, idp):
    auth.logout(request)
    clear_session_idp(request)


def prepare_request(request, idp):
    return {
        "https": "on" if request.is_secure() else "off",
        "http_host": request.get_host(),
        "script_name": request.path_info,
        "server_port": 443 if request.is_secure() else request.get_port(),
        "get_data": request.GET.copy(),
        "post_data": request.POST.copy(),
        "lowercase_urlencoding": idp.lowercase_encoding,
    }


def update_user(request, idp, saml, user, created=None):
    # A dictionary of SAML attributes, mapped to field names via IdPAttribute.
    attrs = idp.mapped_attributes(saml)
    # The set of mapped attributes that should always be updated on the user.
    always_update = set(
        idp.attributes.filter(always_update=True).values_list("mapped_name", flat=True)
    )
    # For users created by this backend, set initial user default values.
    if created:
        attrs.update(
            {default.field: [default.value] for default in idp.user_defaults.all()}
        )
    # Keep track of which fields (if any) were updated.
    update_fields = []
    for field, values in attrs.items():
        if created or field in always_update:
            try:
                f = user._meta.get_field(field)
                # Only update if the field changed. This is a primitive check, but
                # will catch most cases.
                if values[0] != getattr(user, f.attname):
                    setattr(user, f.attname, values[0])
                    update_fields.append(f.name)
            except FieldDoesNotExist:
                pass
    if created or update_fields:
        # Doing a full clean will make sure the values we set are of the correct
        # types before saving.
        user.full_clean(validate_unique=False)
        user.save()
    return user


def get_request_idp(request, **kwargs):
    custom_loader = getattr(settings, "SP_IDP_LOADER", None)
    if custom_loader:
        return import_string(custom_loader)(request, **kwargs)
    else:
        return get_object_or_404(IdP, url_params=kwargs, is_active=True)


def get_session_idp(request):
    return IdP.objects.filter(pk=request.session.get(IDP_SESSION_KEY)).first()


def get_session_nameid(request):
    return request.session.get(NAMEID_SESSION_KEY)


def set_session_idp(request, idp, nameid):
    request.session[IDP_SESSION_KEY] = idp.pk
    request.session[NAMEID_SESSION_KEY] = nameid


def clear_session_idp(request):
    for key in (IDP_SESSION_KEY, NAMEID_SESSION_KEY):
        try:
            del request.session[key]
        except KeyError:
            pass
