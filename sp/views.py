import datetime

from django.conf import settings
from django.contrib import auth
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from .models import IdP


def metadata(request, idp_slug):
    idp = get_object_or_404(IdP, slug=idp_slug, is_active=True)
    saml_settings = OneLogin_Saml2_Settings(settings=idp.sp_settings, sp_validation_only=True)
    return HttpResponse(saml_settings.get_sp_metadata(), content_type="text/xml")


@csrf_exempt
@require_POST
def acs(request, idp_slug):
    idp = get_object_or_404(IdP, slug=idp_slug, is_active=True)
    if request.POST.get("RelayState"):
        state = signing.loads(request.POST["RelayState"], max_age=300)
    else:
        state = {"test": False, "redir": ""}
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    saml.process_response()
    errors = saml.get_errors()
    if errors:
        text = "An error occurred processing your request:\n%s\n%s" % (",".join(errors), saml.get_last_error_reason())
        return HttpResponse(text, content_type="text/plain", status=500)
    else:
        if state.get("test", False):
            attrs = []
            for saml_attr, value in saml.get_attributes().items():
                attr, created = idp.attributes.get_or_create(saml_attribute=saml_attr)
                attrs.append((attr, "; ".join(value)))
            return render(
                request,
                "sp/test.html",
                {"idp": idp, "attrs": attrs, "nameid": saml.get_nameid(), "nameid_format": saml.get_nameid_format()},
            )
        else:
            last_login = timezone.now()
            idp.last_login = last_login
            idp.save(update_fields=("last_login",))
            user = auth.authenticate(request, idp=idp, saml=saml)
            if user:
                auth.login(request, user)
                if idp.respect_expiration and settings.SESSION_SERIALIZER.endswith("PickleSerializer"):
                    try:
                        dt = datetime.datetime.fromtimestamp(saml.get_session_expiration(), tz=datetime.timezone.utc)
                        request.session.set_expiry(dt)
                    except TypeError:
                        pass
            return redirect(idp.get_login_redirect(state.get("redir")))


def login(request, idp_slug, test=False, verify=False):
    idp = get_object_or_404(IdP, slug=idp_slug, is_active=True)
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    reauth = verify or "reauth" in request.GET
    state = signing.dumps({"idp": idp_slug, "test": test, "redir": request.GET.get(auth.REDIRECT_FIELD_NAME, "")})
    return redirect(saml.login(state, force_authn=reauth))
