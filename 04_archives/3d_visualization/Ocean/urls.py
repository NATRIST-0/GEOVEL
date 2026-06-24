# ocean/urls.py
from django.urls import path
from django.shortcuts import redirect
from .Views import coords_view, profiles_view, vectors_view, velocity_view, ekman_view, export_figure

urlpatterns = [
    path("", lambda request: redirect("coords", permanent=False)),      # Accueil
    path("coords/", coords_view, name="coords"),                            # Coordonnées
    path("profiles/<str:var>/", profiles_view, name="profiles"),            # Profiles
    path("velocity/", velocity_view, name="velocity"),                    # Vitesse
    path("vectors/", vectors_view, name="vectors"),                         # Vecteurs
    path("ekman/", ekman_view, name="ekman"),                                # Ekman

    # Export statique
    path("export/<str:kind>/", export_figure, name="export_figure"),
]
