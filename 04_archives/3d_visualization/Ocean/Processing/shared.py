# ocean/processing/shared.py
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from django.conf import settings

from Ocean.Processing.coords import load_xy_from_csv
from Ocean.Processing.cnv import read_cnv_vars
from Ocean.Processing.geo import make_z_grid
from Ocean.Processing.pipeline import (
    STATIONS,
    build_station_series,
    compute_geostrophic_pipeline,
)


def build_all_context(request) -> dict:
    """
    Construit un contexte complet pour toutes les pages.
      - coords.html   → xy_json, meta_json
      - profiles.html → stations_series_json (depth + density/salinity/temperature)
      - velocity.html → z_json, u_json, v_json, z_ref
      - vectors.html  → z_json, u_json, v_json, z_ref
    """
    errors: list[str] = []
    data_dir: Path = getattr(settings, "DATA_DIR")

    # 1) Coordonnées
    try:
        xy, meta = load_xy_from_csv(data_dir / "Coords" / "stations_banyuls.csv")
    except Exception as e:
        xy, meta = {}, {}
        errors.append(f"Erreur lecture stations_banyuls.csv : {e}")

    # 2) Lecture .cnv et préparation séries brutes pour profils
    stations_df = {}
    for name in STATIONS:
        p = data_dir / "Cnv" / f"{name}.cnv"
        if not p.exists():
            errors.append(f"{p.name} manquant dans {p.parent}")
            continue
        try:
            # read_cnv_vars doit renvoyer un DataFrame avec au minimum:
            # ['depth','density'] et si possible ['salinity','temperature']
            df = read_cnv_vars(p)
            stations_df[name] = df
        except Exception as e:
            errors.append(f"{p.name}: {e}")
    stations_series = build_station_series(stations_df)

    # Si on n’a pas les 4 stations, on fournit au moins coords + profils bruts
    if not stations_df or any(s not in stations_df for s in STATIONS):
        return {
            "errors": errors,
            "xy_json": json.dumps(xy),
            "meta_json": json.dumps(meta),
            "stations_series_json": json.dumps(stations_series),
            "z_json": "[]", "u_json": "[]", "v_json": "[]",
            "z_ref": None,
        }

    # 3) Grille verticale commune (intersection des profondeurs)
    z = make_z_grid(stations_df)
    if not len(z):
        errors.append("Aucune profondeur commune entre stations.")
        return {
            "errors": errors,
            "xy_json": json.dumps(xy),
            "meta_json": json.dumps(meta),
            "stations_series_json": json.dumps(stations_series),
            "z_json": "[]", "u_json": "[]", "v_json": "[]",
            "z_ref": None,
        }

    # 4) z_ref borné à [z_min, z_max]
    try:
        z_ref = int(request.GET.get("z_ref", 50))
    except (TypeError, ValueError):
        z_ref = 50
    z_ref = int(np.clip(z_ref, int(z[0]), int(z[-1])))

    # 5) Densité sur la grille + gradients + vent thermique (pour velocity/vectors)
    try:
        result = compute_geostrophic_pipeline(stations_df, xy, meta, z_ref)
        u, v = result["u"], result["v"]
    except Exception as e:
        errors.append(f"Géostrophie : {e}")
        u = np.array([]); v = np.array([])

    # 6) Contexte unique
    return {
        "errors": errors,
        "xy_json": json.dumps(xy),
        "meta_json": json.dumps(meta),
        "stations_series_json": json.dumps(stations_series),  # ← depth + 3 variables
        "z_json": json.dumps(z.tolist()),
        "u_json": json.dumps(u.tolist()),
        "v_json": json.dumps(v.tolist()),
        "z_ref": z_ref,
    }
