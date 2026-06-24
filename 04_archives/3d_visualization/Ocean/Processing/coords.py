# ocean/processing/coords.py
from pathlib import Path
import pandas as pd
import numpy as np

def load_xy_from_csv(csv_path: Path):
    # --- Lecture du fichier CSV ---
    df = pd.read_csv(csv_path)
    if not {"station","lat_deg","lon_deg"} <= set(df.columns):
        raise ValueError("CSV doit contenir station, lat_deg, lon_deg")

    # --- Calcul du barycentre ---
    lat0 = float(df["lat_deg"].mean())
    lon0 = float(df["lon_deg"].mean())

    # --- Conversion des degrés en mètre par rapport au barycentre ---
    kx = 111_320.0 * np.cos(np.deg2rad(lat0))
    ky = 111_320.0
    xs = (df["lon_deg"] - lon0) * kx
    ys = (df["lat_deg"] - lat0) * ky

    # --- Renvoie la liste des coordonnées ---
    xy = {row.station.lower(): (float(x), float(y)) for row, x, y in zip(df.itertuples(), xs, ys)}
    meta = {"lat0": lat0, "lon0": lon0, "kx": float(kx), "ky": float(ky)}
    return xy, meta
