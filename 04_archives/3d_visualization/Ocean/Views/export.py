# ocean/views/export.py
from __future__ import annotations
import io
from pathlib import Path
from django.http import HttpResponse, Http404
from django.conf import settings

import numpy as np

from Ocean.Processing.coords import load_xy_from_csv
from Ocean.Processing.cnv import read_cnv_vars
from Ocean.Processing.geo import make_z_grid
from Ocean.Processing.pipeline import (
    STATIONS,
    compute_geostrophic_pipeline,
    select_column_on_grid,
)
from Ocean.Processing.figures import (
    fig_profiles_static,
    fig_velocity_static,
    fig_vectors_static,
    fig_coords_static,
)


def _mime(fmt: str) -> str:
    """Type MIME en fonction du format demandé."""
    return {
        "png": "image/png",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }[fmt]


def export_figure(request, kind: str):
    """
    Exporte une figure statique (PNG/SVG/PDF) selon `kind` :

      - 'coords'                          → carte des 4 stations + barycentre
      - 'profiles_density'                → profils de densité
      - 'profiles_salinity'               → profils de salinité
      - 'profiles_temperature'            → profils de température
      - 'velocity'                        → u(z), v(z)
      - 'vectors'                         → hodographe (u, v) coloré par z

    Paramètres GET usuels:
      - format = png|svg|pdf   (défaut: png)
      - width, height (pixels) (défaut: 1200 x 800)
      - dpi (défaut: 150)
      - z_ref (m) pour velocity/vectors (défaut: 50)
    """
    # --------- paramètres génériques récupérés dans l'URL ---------
    fmt   = (request.GET.get("format") or "png").lower()
    width = int(request.GET.get("width", 1200))
    height= int(request.GET.get("height", 800))
    dpi   = int(request.GET.get("dpi", 150))

    if fmt not in {"png", "svg", "pdf"}:
        raise Http404("Format non supporté")

    data_dir: Path = getattr(settings, "DATA_DIR")



    # Petit utilitaire : sérialiser/renvoyer une figure avec un nom de fichier propre
    def _response_with_fig(fig, filename: str):
        """Sauve la figure en mémoire, renvoie une réponse HTTP en pièce jointe."""
        buf = io.BytesIO()  # Crée un fichier virtuel en mémoire
        fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
        buf.seek(0)  # revient au début du fichier
        fig.clf(); del fig  # libère la mémoire côté serveur
        response = HttpResponse(buf.getvalue(), content_type=_mime(fmt))  # MIME (Multipurpose Internet Mail Extensions)
        response["Content-Disposition"] = f'attachment; filename="{filename}.{fmt}"'
        return response

    # --------- 1) COORDS : pas besoin des CNV, juste le CSV des positions ---------
    if kind == "coords":
        xy, meta = load_xy_from_csv(data_dir / "Coords" / "stations_banyuls.csv")
        fig = fig_coords_static(xy, meta, width_px=width, height_px=height, dpi=dpi)
        return _response_with_fig(fig, "coords")

    # --------- 2) Lecture CNV + grille commune (pour profils / vitesse / vecteurs) ---------
    stations_df = {}
    for name in STATIONS:
        p = data_dir / "Cnv" / f"{name}.cnv"
        if not p.exists():
            raise Http404(f"Fichier manquant: {p.name}")
        # DataFrame avec colonnes : depth, density, salinity, temperature
        stations_df[name] = read_cnv_vars(p)

    # Grille verticale : intersection exacte des profondeurs présentes aux 4 stations
    z = make_z_grid(stations_df)
    if not len(z):
        raise Http404("Aucune profondeur commune")

    # --------- helper local (sélection de colonnes sur la grille z) ---------
    def _series_on_grid(stations_dict, z_arr, var_key):
        """
        Construit un dict {station: ndarray(var(z))} pour la variable demandée.
        Vérifie que la colonne existe dans chaque DataFrame.
        """
        out = {}
        for st, df in stations_dict.items():
            if var_key not in df.columns:
                raise Http404(f"Colonne absente dans {st}: {var_key}")
            out[st] = select_column_on_grid(df, z_arr, var_key)
        return out

    # --------- 3) PROFILS : un seul des 3 paramètres à la fois ---------
    if kind.startswith("profiles_"):
        var_key = {
            "profiles_density": "density",
            "profiles_salinity": "salinity",
            "profiles_temperature": "temperature",
        }.get(kind)
        if not var_key:
            raise Http404("Type de profil inconnu")

        label = {
            "density": "Densité (kg/m³)",
            "salinity": "Salinité (PSU)",
            "temperature": "Température (°C)",
        }[var_key]

        series = _series_on_grid(stations_df, z, var_key)
        fig = fig_profiles_static(z, series, x_label=label, title=f"Profils de {label}")
        return _response_with_fig(fig, kind)  # ex: profiles_density.png

    # --------- 4) VITESSE / VECTEURS : calcul géostrophique barocline ---------
    # Besoin des coordonnées (pour les gradients) et de la latitude (pour f)
    xy, meta = load_xy_from_csv(data_dir / "Coords" / "stations_banyuls.csv")

    # Profondeur de référence (vitesse nulle)
    try:
        z_ref = int(request.GET.get("z_ref", 50))
    except (TypeError, ValueError):
        z_ref = 50
    z_ref = int(np.clip(z_ref, int(z[0]), int(z[-1])))

    # Vent thermique + intégration : profils u(z), v(z)
    result = compute_geostrophic_pipeline(stations_df, xy, meta, z_ref)
    z_ref, u, v = result["z_ref"], result["u"], result["v"]

    # Figure demandée
    if kind == "velocity":
        fig = fig_velocity_static(z, u, v, z_ref)  # deux panneaux u/v
        return _response_with_fig(fig, "velocity")
    elif kind == "vectors":
        fig = fig_vectors_static(z, u, v, z_ref)  # hodographe
        return _response_with_fig(fig, "vectors")
    else:
        raise Http404("Figure inconnue")
