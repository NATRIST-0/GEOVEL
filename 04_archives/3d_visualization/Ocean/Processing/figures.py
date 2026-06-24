# ocean/processing/figures.py
import math
import numpy as np
import matplotlib.pyplot as plt

# ---------- COORDS ----------
def fig_coords_static(xy: dict, meta: dict, width_px=1200, height_px=800, dpi=150):
    fig_w = width_px / dpi
    fig_h = height_px / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    # points stations
    names = ["nord", "est", "sud", "ouest"]
    xs = [xy[n][0] for n in names if n in xy]
    ys = [xy[n][1] for n in names if n in xy]
    ax.scatter(xs, ys, s=70, c=["#3b82f6", "#10b981", "#f59e0b", "#ef4444"],
               label="Stations", zorder=3)

    # barycentre
    ax.scatter([0], [0], s=120, c="#111827", marker="x",
               label="Barycentre", zorder=4)

    # noms
    for n, x, y in zip(names, xs, ys):
        ax.text(x, y, f" {n.capitalize()}", va="bottom", fontsize=10)

    # axes principaux
    ax.axhline(0, color="#334155", lw=1.2, alpha=0.9, zorder=1)
    ax.axvline(0, color="#334155", lw=1.2, alpha=0.9, zorder=1)

    ax.set_xlabel("Est (m)")
    ax.set_ylabel("Nord (m)")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.set_title("Stations et barycentre (repère local)")
    ax.legend(frameon=False)
    return fig


# ---------- PROFILS ----------
def fig_profiles_static(z: np.ndarray, series: dict[str, np.ndarray],
                        x_label="Densité (kg/m³)", title="Profils"):
    import numpy as np
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    colors = {"nord":"#3b82f6","est":"#10b981","sud":"#f59e0b","ouest":"#ef4444"}

    # tracer
    for name, xvals in series.items():
        ax.plot(np.asarray(xvals, float), np.asarray(z, float),
                lw=2, color=colors.get(name, "#444"),
                label=name.capitalize())

    # y: profondeur 0 en haut (bornes serrées)
    z = np.asarray(z, float)
    ax.set_ylim(np.max(z), np.min(z))
    ax.set_ylabel("Profondeur (m)")

    # x: autoscale + marge
    all_x = np.concatenate([np.asarray(v, float) for v in series.values()]) if series else np.array([])
    if all_x.size:
        x_min = float(np.nanmin(all_x))
        x_max = float(np.nanmax(all_x))
        rng = x_max - x_min
        if rng <= 0:  # toutes les valeurs (quasi) identiques
            # marge absolue minimale en fonction de l’ordre de grandeur
            pad = max(0.02 * max(1.0, abs(x_max)), 0.1)
            ax.set_xlim(x_min - pad, x_max + pad)
        else:
            pad = 0.05 * rng  # 5 %
            ax.set_xlim(x_min - pad, x_max + pad)

    ax.set_xlabel(x_label)
    ax.set_title(title)
    # grille + axes 0 en gris foncé pour ressortir (si dans le domaine)
    ax.grid(True, alpha=0.25)
    ax.axvline(0, color="#374151", lw=1)
    ax.axhline(0, color="#374151", lw=1)
    ax.legend(frameon=False)
    return fig


# ---------- VITESSES u/v ----------
def fig_velocity_static(z: np.ndarray, u: np.ndarray, v: np.ndarray, z_ref: float):
    u_cm = np.asarray(u) * 100.0
    v_cm = np.asarray(v) * 100.0
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), dpi=150, sharey=True)

    # --- profil u
    axes[0].plot(u_cm, z, color="#2563eb", lw=2)
    axes[0].set_title("u (cm/s)")
    axes[0].grid(True, alpha=0.25)
    axes[0].set_xlabel("cm/s")
    axes[0].axvline(0, color="#334155", lw=1.2, alpha=0.9)

    # --- profil v
    axes[1].plot(v_cm, z, color="#16a34a", lw=2)
    axes[1].set_title("v (cm/s)")
    axes[1].grid(True, alpha=0.25)
    axes[1].set_xlabel("cm/s")
    axes[1].axvline(0, color="#334155", lw=1.2, alpha=0.9)

    axes[0].set_ylabel("Profondeur (m)")
    axes[0].set_ylim(max(z), min(z))  # 0 en haut
    fig.suptitle(f"Profils de vitesse géostrophique (réf. z_ref = {int(z_ref)} m)")
    fig.tight_layout()
    return fig


# ---------- VECTEURS ----------
def fig_vectors_static(z: np.ndarray, u: np.ndarray, v: np.ndarray, z_ref: float):
    u_cm = np.asarray(u) * 100.0
    v_cm = np.asarray(v) * 100.0

    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

    # segments gris pâles
    for uu, vv in zip(u_cm, v_cm):
        ax.plot([0, uu], [0, vv], color="0.6", lw=1, alpha=0.6)

    # points colorés (échelle inversée)
    sc = ax.scatter(u_cm, v_cm, c=z, cmap="viridis_r", s=35, zorder=3)

    # colorbar
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Profondeur (m)")
    cbar.ax.invert_yaxis()  # 🔹 inversion verticale : 0 en haut, fond en bas

    # limites symétriques
    amax = max(10, math.ceil(max(np.max(np.abs(u_cm)), np.max(np.abs(v_cm))) / 5) * 5)
    ax.set_xlim(-amax, amax)
    ax.set_ylim(-amax, amax)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)

    # axes principaux visibles
    ax.axhline(0, color="#334155", lw=1.2, alpha=0.9)
    ax.axvline(0, color="#334155", lw=1.2, alpha=0.9)

    ax.set_xlabel("u (cm/s)")
    ax.set_ylabel("v (cm/s)")
    ax.set_title(f"Vecteurs (réf. z_ref = {int(z_ref)} m)")
    return fig
