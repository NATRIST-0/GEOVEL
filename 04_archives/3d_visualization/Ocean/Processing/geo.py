# ocean/processing/geo.py
from __future__ import annotations
import numpy as np
import pandas as pd


def make_z_grid(stations: dict[str, pd.DataFrame]) -> np.ndarray:
    """
    Renvoie la grille verticale commune aux stations.
    Intersection exacte des profondeurs présentes dans toutes les stations.
    """
    depth_sets = []
    for df in stations.values():
        d = df["depth"].to_numpy(dtype=int)
        depth_sets.append(set(d.tolist()))

    common = set.intersection(*depth_sets)

    return np.array(sorted(common), dtype=int)


def select_on_grid(df: pd.DataFrame, z: np.ndarray) -> np.ndarray:
    """
    Sélection directe des densités aux profondeurs z.
    Suppose que chaque profondeur z est présente dans df.
    """
    g = df.set_index("depth")["density"]
    return g.loc[z].to_numpy(dtype=float)


def compute_rho0_mean(
    stations: dict[str, pd.DataFrame],
) -> float:
    """
    Calcule une densité de référence ρ0 comme MOYENNE des densités observées.
    Retourne un float (kg/m^3).
    """
    if not stations:
        return 1025.0  # fallback raisonnable

    z = make_z_grid(stations)

    # Empile ρ(z) pour chaque station sur la grille commune
    vals = []
    for df in stations.values():
        rho = select_on_grid(df, z)  # ndarray float
        vals.append(rho)
    all_vals = np.concatenate(vals)
    return float(np.nanmean(all_vals))


def fit_plane_gradient(xy: np.ndarray, rho: np.ndarray) -> tuple[float, float]:
    """
    Résolution au sens des moindres carrés de ρ(x,y) = a x + b y + c avec 4 points (stations).
    Retourne (∂ρ/∂x, ∂ρ/∂y) = (a, b).
    """
    a_mat = np.c_[xy[:, 0], xy[:, 1], np.ones_like(rho, dtype=int)]
    a, b, _ = np.linalg.lstsq(a_mat, rho)[0]
    return float(a), float(b)


def geostrophic_from_density_grad(
    drdx: np.ndarray,
    drdy: np.ndarray,
    z: np.ndarray,
    f: float,
    rho0: float = 1025.0,
    g: float = 9.81,
    z_ref: int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Vent thermique avec u(z_ref)=v(z_ref)=0.
    """
    if f == 0:
        raise ValueError("Le paramètre de Coriolis f ne peut pas être nul.")

    if not (drdx.shape == drdy.shape == z.shape):
        raise ValueError("Dimensions incompatibles entre drdx_z, drdy_z et z.")

    # 1) Vent thermique (dérivées verticales)
    coef  = g / (f * rho0)
    dudz = -coef * drdy
    dvdz =  coef * drdx

    # 2) Intégration verticale depuis la surface (trapèzes)
    m_du = 0.5 * (dudz[:-1] + dudz[1:])
    m_dv = 0.5 * (dvdz[:-1] + dvdz[1:])

    # 3) Intégrales cumulées depuis la surface
    u_cum = np.concatenate(([0.0], np.cumsum(m_du)))
    v_cum = np.concatenate(([0.0], np.cumsum(m_dv)))

    # 4) Condition u(z_ref) = v(z_ref) = 0
    iref = int(np.argmin(np.abs(z - z_ref)))
    u = u_cum - u_cum[iref]
    v = v_cum - v_cum[iref]

    return u, v
