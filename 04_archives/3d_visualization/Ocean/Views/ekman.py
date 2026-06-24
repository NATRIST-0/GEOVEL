# ocean/views/ekman.py
import json
from pathlib import Path
from django.shortcuts import render
from django.conf import settings

from Ocean.Processing.coords import load_xy_from_csv
from Ocean.Processing.ekman import compute_surface_ekman


def ekman_view(request):
    """
    Page simple : courants d’Ekman de surface
    V0 = T / (rho_eau * sqrt(f * Az)),   T = rho_air * Cd * |U10|^2

    Convention ici :
      - wind_dir (deg) = direction VERS laquelle souffle le vent,
        0 = vers le nord, 90 = vers l’est (x est, y nord).
      - En hémisphère nord, le courant de surface est dévié +45° à DROITE du vent.
    """
    data_dir: Path = getattr(settings, "DATA_DIR")

    # Latitude moyenne
    _, meta = load_xy_from_csv(data_dir / "Coords" / "stations_banyuls.csv")
    phi_deg = float(meta.get("lat0"))

    # Récup paramètres (GET) avec valeurs par défaut classiques
    def get_float(name: str, default: float) -> float:
        try:
            return float(request.GET.get(name, default))
        except (TypeError, ValueError):
            return default

    U10     = get_float("U10", 8.0)          # m/s
    Cd      = get_float("Cd", 1.5e-3)        # Sans unité
    rho_air = get_float("rho_air", 1.3)      # kg/m3
    rho_eau = get_float("rho_eau", 1025.0)   # kg/m3
    Az      = get_float("Az", 0.01)          # m2/s (viscosité turbulente)
    wind_dir= get_float("wind_dir", 0.0)     # deg (VERS laquelle souffle le vent)
    phi_deg = get_float("lat", phi_deg)             # permet de surcharger la latitude si besoin

    result = compute_surface_ekman(
        wind_speed=U10,
        drag_coefficient=Cd,
        air_density=rho_air,
        water_density=rho_eau,
        eddy_viscosity=Az,
        wind_direction=wind_dir,
        latitude=phi_deg,
    )

    context = {
        "errors": result["errors"],
        "params": json.dumps({
            "U10": U10, "Cd": Cd, "rho_air": rho_air, "rho_eau": rho_eau,
            "Az": Az, "wind_dir": wind_dir, "lat": phi_deg, "f": result["f"],
            "T": result["wind_stress"], "V0": result["surface_speed"]
        }),
        "wind_vec": json.dumps(result["wind_vector"]),
        "ekman_vec": json.dumps(result["ekman_vector"]),
    }
    return render(request, "Ocean/ekman.html", context)
