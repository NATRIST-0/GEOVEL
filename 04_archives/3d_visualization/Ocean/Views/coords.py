# ocean/views/coords.py
from django.shortcuts import render
from Ocean.Processing.shared import build_all_context

def coords_view(request):
    return render(request, "Ocean/coords.html", build_all_context(request))
