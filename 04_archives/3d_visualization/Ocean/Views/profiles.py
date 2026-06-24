# ocean/views/profiles.py
from django.shortcuts import render
from Ocean.Processing.shared import build_all_context

def profiles_view(request, var: str = "density"):
    ctx = build_all_context(request)
    if var not in {"density", "salinity", "temperature"}:
        var = "density"
    ctx["active_var"] = var
    return render(request, "Ocean/profiles.html", ctx)
