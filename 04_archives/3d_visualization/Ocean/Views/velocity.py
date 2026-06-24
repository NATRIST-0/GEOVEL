# ocean/views/velocity.py
from django.shortcuts import render
from Ocean.Processing.shared import build_all_context

def velocity_view(request):
    context = build_all_context(request)
    return render(request, "Ocean/velocity.html", context)
