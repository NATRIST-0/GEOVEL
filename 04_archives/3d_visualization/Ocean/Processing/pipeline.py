from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from Ocean.Processing.cnv import read_cnv_vars
from Ocean.Processing.coords import load_xy_from_csv
from Ocean.Processing.geo import (
    compute_rho0_mean,
    fit_plane_gradient,
    geostrophic_from_density_grad,
    make_z_grid,
    select_on_grid,
)


STATIONS = ("nord", "est", "sud", "ouest")


def load_station_profiles(
    cnv_paths: Mapping[str, Path],
) -> dict[str, pd.DataFrame]:
    """Charge les quatre profils CNV dans l'ordre attendu par le calcul."""
    return {station: read_cnv_vars(Path(cnv_paths[station])) for station in STATIONS}


def build_station_series(
    stations: Mapping[str, pd.DataFrame],
) -> dict[str, dict[str, list]]:
    """Prépare les profils complets pour leur sérialisation ou leur affichage."""
    series = {}
    for station, df in stations.items():
        series[station] = {
            "depth": df["depth"].tolist(),
            "density": df["density"].tolist() if "density" in df.columns else [],
            "salinity": df["salinity"].tolist() if "salinity" in df.columns else [],
            "temperature": (
                df["temperature"].tolist() if "temperature" in df.columns else []
            ),
        }
    return series


def select_column_on_grid(
    df: pd.DataFrame,
    z: np.ndarray,
    column: str,
) -> np.ndarray:
    """Sélectionne une variable aux profondeurs entières de la grille commune."""
    values = df.set_index(df["depth"].astype(int))[column]
    return np.array([float(values.loc[int(depth)]) for depth in z], dtype=float)


def compute_geostrophic_pipeline(
    stations: Mapping[str, pd.DataFrame],
    xy: Mapping[str, tuple[float, float]],
    meta: Mapping[str, float],
    z_ref: int = 50,
) -> dict:
    """Orchestre le calcul géostrophique à partir de données déjà chargées."""
    z = make_z_grid(dict(stations))
    if not len(z):
        raise ValueError("Aucune profondeur commune entre stations.")

    z_ref = int(np.clip(z_ref, int(z[0]), int(z[-1])))
    densities = {
        station: select_on_grid(stations[station], z) for station in STATIONS
    }
    xy_matrix = np.array([xy[station] for station in STATIONS], dtype=float)

    drdx = np.zeros_like(z, dtype=float)
    drdy = np.zeros_like(z, dtype=float)
    for index in range(len(z)):
        density_at_depth = np.array(
            [densities[station][index] for station in STATIONS],
            dtype=float,
        )
        drdx[index], drdy[index] = fit_plane_gradient(
            xy_matrix,
            density_at_depth,
        )

    latitude = float(meta.get("lat0", 42.48))
    coriolis = 2.0 * 7.2921e-5 * np.sin(np.deg2rad(latitude))
    rho0 = compute_rho0_mean(dict(stations))
    u, v = geostrophic_from_density_grad(
        drdx,
        drdy,
        z,
        coriolis,
        rho0,
        9.81,
        z_ref,
    )

    return {
        "z": z,
        "z_ref": z_ref,
        "drdx": drdx,
        "drdy": drdy,
        "rho0": rho0,
        "f": coriolis,
        "u": u,
        "v": v,
    }


def run_geostrophic_pipeline(
    coordinates_path: Path,
    cnv_paths: Mapping[str, Path],
    z_ref: int = 50,
) -> dict:
    """Charge les fichiers explicites et exécute le pipeline hors Django."""
    xy, meta = load_xy_from_csv(Path(coordinates_path))
    stations = load_station_profiles(cnv_paths)
    result = compute_geostrophic_pipeline(stations, xy, meta, z_ref)
    result.update(
        {
            "xy": xy,
            "meta": meta,
            "stations": stations,
            "station_series": build_station_series(stations),
        }
    )
    return result
