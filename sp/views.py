from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from .utils import get_request_idp, get_session_nameid, get_session_nameid_format


def metadata(request, **kwargs):
    idp = get_request_idp(request, **kwargs)
    print(idp.sp_settings)
    
    saml_settings = OneLogin_Saml2_Settings(
        settings=idp.sp_settings, sp_validation_only=True
    )
    return HttpResponse(saml_settings.get_sp_metadata(), content_type="text/xml")


@csrf_exempt
@require_POST
def acs(request, **kwargs):
    idp = get_request_idp(request, **kwargs)
    state = request.POST.get("RelayState")
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    saml.process_response()
    errors = saml.get_errors()
    if errors:
        return render(
            request,
            "sp/error.html",
            {
                "idp": idp,
                "state": state,
                "errors": errors,
                "reason": saml.get_last_error_reason(),
            },
            status=500,
        )
    else:
        if state and state.startswith("test:"):
            attrs = []
            for saml_attr, value in saml.get_attributes().items():
                attr, created = idp.attributes.get_or_create(saml_attribute=saml_attr)
                attrs.append((attr, "; ".join(value)))
            return render(
                request,
                "sp/test.html",
                {
                    "idp": idp,
                    "attrs": attrs,
                    "nameid": saml.get_nameid(),
                    "nameid_format": saml.get_nameid_format(),
                    "redir": state[5:],
                },
            )
        elif state and state.startswith("verify:"):
            user = idp.authenticate(request, saml)
            if user == request.user:
                # TODO: add a hook here
                return redirect(idp.get_login_redirect(state[7:]))
            else:
                return render(
                    request,
                    "sp/unauth.html",
                    {
                        "nameid": idp.get_nameid(saml),
                        "idp": idp,
                        "verify": True,
                    },
                    status=401,
                )
        else:
            user = idp.authenticate(request, saml)
            if user:
                if isinstance(user, HttpResponseBase):
                    return user
                else:
                    idp.login(request, user, saml)
                    idp.last_login = timezone.now()
                    idp.save(update_fields=("last_login",))
                    return redirect(idp.get_login_redirect(state))
            else:
                return render(
                    request,
                    "sp/unauth.html",
                    {
                        "nameid": idp.get_nameid(saml),
                        "idp": idp,
                        "verify": False,
                    },
                    status=401,
                )


def slo(request, **kwargs):
    idp = get_request_idp(request, **kwargs)
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    state = request.GET.get("RelayState")
    redir = saml.process_slo()
    errors = saml.get_errors()
    if errors:
        return render(
            request,
            "sp/error.html",
            {
                "idp": idp,
                "state": state,
                "errors": errors,
                "reason": saml.get_last_error_reason(),
            },
            status=500,
        )
    else:
        idp.logout(request)
        if not redir:
            redir = idp.get_logout_redirect(state)
        return redirect(redir)


def login(request, test=False, verify=False, **kwargs):
    idp = get_request_idp(request, **kwargs)
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    reauth = verify or "reauth" in request.GET
    redir = request.GET.get(REDIRECT_FIELD_NAME, "")
    # SAML only allows RelayState to be 80 characters, make them count.
    if test:
        state = "test:" + redir
    elif verify:
        state = "verify:" + redir
    else:
        state = redir
    # When verifying, we want to pass the (unmapped) SAML nameid, stored in the session.
    # TODO: do we actually want UPN here, or some other specified mapped field? At least
    # Auth0 is pre-populating the email field with nameid, which is not what we want.
    nameid = get_session_nameid(request) if verify else None
    return redirect(saml.login(state, force_authn=reauth, name_id_value_req=nameid))


def logout(request, **kwargs):
    idp = get_request_idp(request, **kwargs)
    redir = idp.get_logout_redirect(request.GET.get(REDIRECT_FIELD_NAME))
    saml = OneLogin_Saml2_Auth(idp.prepare_request(request), old_settings=idp.settings)
    if saml.get_slo_url() and idp.logout_triggers_slo:
        # If the IdP supports SLO, send it a logout request (it will call our SLO).
        return redirect(
            saml.logout(
                redir,
                name_id=get_session_nameid(request),
                name_id_format=get_session_nameid_format(request),
            )
        )
    else:
        # Handle the logout "locally", i.e. log out via django.contrib.auth by default.
        idp.logout(request)
        return redirect(redir)
