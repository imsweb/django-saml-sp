from django.shortcuts import render

from sp.models import SP


def home(request):
    return render(request, "home.html", {"sps": SP.objects.filter(is_active=True)})
