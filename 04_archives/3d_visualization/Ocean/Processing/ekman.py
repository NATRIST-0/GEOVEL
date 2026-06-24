from __future__ import annotations

import numpy as np


def compute_surface_ekman(
    wind_speed: float,
    drag_coefficient: float,
    air_density: float,
    water_density: float,
    eddy_viscosity: float,
    wind_direction: float,
    latitude: float,
) -> dict:
    """Calcule le courant d'Ekman de surface avec les conventions historiques."""
    errors: list[str] = []

    omega = 7.2921e-5
    coriolis = 2.0 * omega * np.sin(np.deg2rad(latitude))
    if coriolis == 0:
        errors.append("Le paramètre de Coriolis f est nul à cette latitude.")
        coriolis = 1e-10

    wind_stress = air_density * drag_coefficient * wind_speed**2
    try:
        surface_speed = wind_stress / (
            water_density * np.sqrt(coriolis * eddy_viscosity)
        )
    except FloatingPointError:
        errors.append("Erreur de calcul : vérifier f et Az.")
        surface_speed = 0.0

    wind_angle = np.deg2rad(wind_direction)
    current_angle = np.deg2rad(wind_direction + 45.0)

    return {
        "errors": errors,
        "f": coriolis,
        "wind_stress": wind_stress,
        "surface_speed": surface_speed,
        "wind_vector": {
            "x": float(wind_speed * np.sin(wind_angle)),
            "y": float(wind_speed * np.cos(wind_angle)),
            "speed": wind_speed,
        },
        "ekman_vector": {
            "x": float(surface_speed * np.sin(current_angle)),
            "y": float(surface_speed * np.cos(current_angle)),
            "speed": surface_speed,
        },
    }
