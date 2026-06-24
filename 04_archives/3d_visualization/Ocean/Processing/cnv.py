# ocean/processing/cnv.py
import re
from pathlib import Path
import pandas as pd


def read_cnv_vars(path: Path):
    """
    Lecture d’un fichier Sea-Bird .cnv
    → renvoie un DataFrame avec :
       - depth (m)
       - density (kg/m^3)        si présent
       - salinity (PSU)          si présent
       - temperature (°C ITS-90) si présent
    Approximation : 1 dbar ≈ 1 m.
    """

    # --- Extraction de l'en-tête ---
    header = []
    with path.open("r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            header.append(line.rstrip("\n"))
            if line.startswith("*END*"):
                break

    # --- Extraction des noms de colonnes ---
    names = []
    for h in header:
        m = re.search(r"#\s*name\s*\d+\s*=\s*([^:]+):", h)
        if m:
            names.append(m.group(1).strip())

    # --- Lecture du tableau de données ---
    df = pd.read_csv(
        path,
        sep=r"\s+",            # séparateur = espaces multiples
        names=names,           # noms de colonnes extraits du header
        skiprows=len(header),  # saute l'entête
    )

    # --- Détection des colonnes principales ---
    if "prdM" not in df.columns:
        raise ValueError(f"Aucune colonne pression trouvée dans {path.name}")

    pr_col = "prdM"
    dens_col = "density00" if "density00" in df.columns else None
    sal_col = "sal00" if "sal00" in df.columns else None
    temp_col = "tv290C" if "tv290C" in df.columns else None

    # --- Nettoyage + renommage cohérent ---
    keep_cols = [pr_col]
    rename_map = {pr_col: "pressure_dbar"}

    if dens_col:
        keep_cols.append(dens_col)
        rename_map[dens_col] = "density"

    if sal_col:
        keep_cols.append(sal_col)
        rename_map[sal_col] = "salinity"

    if temp_col:
        keep_cols.append(temp_col)
        rename_map[temp_col] = "temperature"

    out = df[keep_cols].dropna().copy()
    out.rename(columns=rename_map, inplace=True)

    # --- Conversion pression (dbar) -> profondeur (m) ---
    out["depth"] = out["pressure_dbar"]

    # --- Vérifie que la profondeur croît (surface -> fond) ---
    if len(out) > 1 and out["depth"].iloc[0] > out["depth"].iloc[-1]:
        out = out.iloc[::-1].reset_index(drop=True)

    # --- Retourne le DataFrame complet (colonnes dispo) ---
    cols = ["depth"]
    for c in ["density", "salinity", "temperature"]:
        if c in out.columns:
            cols.append(c)

    return out[cols]
