# ocean/views/vectors.py
from django.shortcuts import render
from Ocean.Processing.shared import build_all_context

def vectors_view(request):
    context = build_all_context(request)
    return render(request, "Ocean/vectors.html", context)
