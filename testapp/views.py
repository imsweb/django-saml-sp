from django.shortcuts import render
from sp.models import IdP
from sp.utils import get_session_idp


def home(request):
    return render(request, "home.html", {"idp": get_session_idp(request), "idps": IdP.objects.filter(is_active=True)})
