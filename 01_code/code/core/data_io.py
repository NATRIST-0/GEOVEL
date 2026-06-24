import re
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations


def read_cnv_files(path: Path, lat: float = None, lon: float = None) -> pd.DataFrame:
    """
    Reading a sea-bird .cnv file
    arguments:
    path: path to the sea-bird file
    lat: latitude where the data was acquired
    lon: longitude where the data was acquired
    returns:
    dataframe containing:
       - depth (m)
       - density (kg/m^3)
       - salinity (PSU)
       - temperature (degC ITS-90)
       - latitude (deg)
       - longitude (deg)
       - source_file
    author: Pierre P.
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
        sep=r"\s+",  # séparateur = espaces multiples
        names=names,  # noms de colonnes extraits du header
        skiprows=len(header),  # saute l'entête
    )

    # --- Détection des colonnes principales ---
    if "prdM" not in df.columns:
        raise ValueError(f"Pressure column not found in {path.name}")

    pr_col = "prdM"
    dens_col = "density00" if "density00" in df.columns else None
    sal_col = "sal00" if "sal00" in df.columns else None
    temp_col = "tv290C" if "tv290C" in df.columns else None

    # --- Nettoyage + renommage cohérent ---
    keep_cols = [pr_col]
    rename_map = {pr_col: "pressure_dbar"}

    if dens_col:
        keep_cols.append(dens_col)
        rename_map[dens_col] = "density (kg/m^3)"

    if sal_col:
        keep_cols.append(sal_col)
        rename_map[sal_col] = "salinity (PSU)"

    if temp_col:
        keep_cols.append(temp_col)
        rename_map[temp_col] = "temperature (degC)"

    out = df[keep_cols].dropna().copy()
    out.rename(columns=rename_map, inplace=True)

    # --- Conversion pression (dbar) -> profondeur (m) ---
    out["depth_m"] = out["pressure_dbar"]

    # --- Vérifie que la profondeur croît (surface -> fond) ---
    if len(out) > 1 and out["depth_m"].iloc[0] > out["depth_m"].iloc[-1]:
        out = out.iloc[::-1].reset_index(drop=True)

    # --- Retourne le DataFrame complet (colonnes dispo + metadata) ---
    cols = ["depth_m"]
    for c in ["density (kg/m^3)", "salinity (PSU)", "temperature (degC)"]:
        if c in out.columns:
            cols.append(c)

    final_df = out[cols].copy()

    # --- Ajout de la localisation et nom du fichier source ---
    final_df["source_file"] = path.name
    if lat is not None:
        final_df["latitude (deg)"] = lat
    if lon is not None:
        final_df["longitude (deg)"] = lon

    return final_df


def derive_plane_equations(df: pd.DataFrame) -> tuple:
    """
    Calculates the horizontal density gradients (dp/dx, dp/dy) for all possible triangles of stations.

    Returns:
    - Tuple containing:
      1. The cleaned DataFrame with density gradients appended (no repetitive metadata).
      2. A metadata dictionary with station coordinates and triangle definitions.
    """

    df = df.copy()

    # Define conversion factors from degrees to kilometers
    lon_to_km = 111.320
    lat_to_km = 110.574

    # Calculate the barycenter to use as the local origin reference
    lat_ref = df["latitude (deg)"].mean()
    lon_ref = df["longitude (deg)"].mean()

    # Convert geographic coordinates into a local metric Cartesian system
    df["x_meters"] = (
        (df["longitude (deg)"] - lon_ref)
        * lon_to_km
        * 1000
        * np.cos(np.radians(lat_ref))
    )
    df["y_meters"] = (df["latitude (deg)"] - lat_ref) * lat_to_km * 1000

    # Initialize the metadata dictionary
    metadata = {"stations": {}, "triangles": {}}

    # Extract static station metadata
    station_meta_df = df[
        ["source_file", "latitude (deg)", "longitude (deg)", "x_meters", "y_meters"]
    ].drop_duplicates()
    for _, row in station_meta_df.iterrows():
        metadata["stations"][row["source_file"]] = {
            "latitude": row["latitude (deg)"],
            "longitude": row["longitude (deg)"],
            "x_meters": row["x_meters"],
            "y_meters": row["y_meters"],
        }

    # Filter out data below the shallowest station to ensure all points exist at a given depth
    min_max_depth = df.groupby("source_file")["depth_m"].max().min()
    df_filtered = df[df["depth_m"] <= min_max_depth]

    # Generate all possible triangles from the available stations
    stations = df_filtered["source_file"].unique()
    triangles = list(combinations(stations, 3))

    # Populate triangle metadata definitions
    for i, triangle_stations in enumerate(triangles):
        t_id = f"T{i + 1}"
        metadata["triangles"][t_id] = "_".join(Path(s).stem for s in triangle_stations)

    results = []

    # Iterate through each depth layer to solve the plane equations
    for depth, group in df_filtered.groupby("depth_m"):
        if len(group) < 3:
            continue

        for i, triangle_stations in enumerate(triangles):
            triangle_data = group[group["source_file"].isin(triangle_stations)]

            if len(triangle_data) == 3:
                x = triangle_data["x_meters"].values
                y = triangle_data["y_meters"].values
                z = triangle_data["density (kg/m^3)"].values

                M = np.c_[x, y, np.ones(3)]

                try:
                    coeffs = np.linalg.solve(M, z)
                    results.append(
                        {
                            "depth_m": depth,
                            "triangle_id": f"T{i + 1}",
                            "dp_dx": coeffs[0],
                            "dp_dy": coeffs[1],
                        }
                    )
                except np.linalg.LinAlgError:
                    pass

    # Convert the results into a dataframe and pivot to align triangles side by side
    results_df = pd.DataFrame(results)

    if not results_df.empty:
        # Pivot gradients by triangle_id
        pivot_df = results_df.pivot(
            index="depth_m", columns="triangle_id", values=["dp_dx", "dp_dy"]
        )
        # Flatten the multi level columns into a single string format like 'dp_dx_Ti'
        pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
        pivot_df = pivot_df.reset_index()

        # Merge the gradient columns back into the primary dataframe
        final_df = pd.merge(df, pivot_df, on="depth_m", how="left")
    else:
        final_df = df

    # Drop the repetitive coordinates from final_df to save massive amounts of space
    cols_to_drop = ["latitude (deg)", "longitude (deg)", "x_meters", "y_meters"]
    final_df = final_df.drop(columns=cols_to_drop)

    return final_df, metadata


def export_processed_data(df: pd.DataFrame, metadata: dict, output_path: str):
    """
    Saves the processed DataFrame to a CSV file.
    Writes the static metadata as a commented header to avoid repetition in the rows.
    Rounds numeric columns.
    """
    df_rounded = df.copy()
    for col in df_rounded.select_dtypes(include=[np.number]).columns:
        fmt = "{0:.8g}" if col == "density (kg/m^3)" else "{0:.4g}"

        def _format_num(x):
            try:
                return x if pd.isna(x) else float(fmt.format(x))
            except Exception:
                return x

        df_rounded[col] = df_rounded[col].apply(_format_num)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("# === Stations Metadata ===\n")
        for station, data in metadata["stations"].items():

            def _fmt(v):
                return f"{float(f'{v:.4g}') if pd.notna(v) and (isinstance(v, (int, float, np.number)) or (isinstance(v, str) and re.match(r'^-?\\d+(\\.\\d+)?$', v))) else v}"

            lat_s = data.get("latitude")
            lon_s = data.get("longitude")
            
            x_s = _fmt(data.get("x_meters"))
            y_s = _fmt(data.get("y_meters"))

            file.write(f"# {station}: Lat={lat_s}, Lon={lon_s}, X={x_s}, Y={y_s}\n")

        file.write("# === Triangles Metadata ===\n")
        for t_id, t_from in metadata["triangles"].items():
            file.write(f"# triangle_{t_id}_from: {t_from}\n")

        file.write("# =========================\n")

    # Append the main dataframe without writing the header index
    df_rounded.to_csv(output_path, mode="a", index=False)