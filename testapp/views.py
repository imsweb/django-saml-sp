from django.shortcuts import render

from sp.models import IdP


def home(request):
    idp = IdP.objects.filter(slug=request.session.get("idp")).first()
    return render(request, "home.html", {"idp": idp, "idps": IdP.objects.filter(is_active=True)})
