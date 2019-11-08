from django.shortcuts import render

from sp.models import IdP


def home(request):
    return render(request, "home.html", {"idps": IdP.objects.filter(is_active=True)})
