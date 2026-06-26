import numpy as np
import pandas as pd
from pathlib import Path

def derive_geostrophic_velocity(file_path: Path) -> pd.DataFrame:
    header_lines = []
    latitudes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                header_lines.append(line)
                if "Lat=" in line:
                    try:
                        lat_str = line.split("Lat=")[1].split(",")[0]
                        latitudes.append(float(lat_str))
                    except (IndexError, ValueError):
                        pass
            else:
                break
                
    if not latitudes:
        raise ValueError("Could not find latitude metadata in the file header.")
        
    mean_lat = np.mean(latitudes)
    df = pd.read_csv(file_path, comment='#')

    g = 9.81 
    rho_0 = 1025.0 
    omega = 7.2921e-5 
    f = 2 * omega * np.sin(np.radians(mean_lat))

    grad_cols = [col for col in df.columns if "drho_" in col or "dsv_" in col]
    cols_to_keep = ["depth_m"] + grad_cols
    
    depth_df = df[cols_to_keep].drop_duplicates(subset=["depth_m"]).copy()
    depth_df = depth_df.sort_values("depth_m").reset_index(drop=True)

    dz = depth_df["depth_m"].diff().fillna(0)
    dp = dz * 10000.0 
    thermal_wind_coef = g / (rho_0 * f)

    # --- Method 1: Isobaric (Array-wide Specific Volume over pressure) ---
    if "dsv_dx" in depth_df.columns and "dsv_dy" in depth_df.columns:
        dv_x_isob = -(1 / f) * depth_df["dsv_dy"] * dp
        dv_y_isob = (1 / f) * depth_df["dsv_dx"] * dp
        
        depth_df["vx_isob_array_cm_s"] = dv_x_isob.cumsum() * 100
        depth_df["vy_isob_array_cm_s"] = dv_y_isob.cumsum() * 100

    # --- Method 2: Isopycnal (Density over depth by Triangles) ---
    num_triangles = len([col for col in depth_df.columns if "drho_dx_T" in col])
    for i in range(1, num_triangles + 1):
        if f"drho_dx_T{i}" not in depth_df.columns:
            continue
            
        dv_x_isop = thermal_wind_coef * depth_df[f"drho_dy_T{i}"] * dz
        dv_y_isop = -thermal_wind_coef * depth_df[f"drho_dx_T{i}"] * dz
        
        depth_df[f"vx_isop_T{i}_cm_s"] = dv_x_isop.cumsum() * 100
        depth_df[f"vy_isop_T{i}_cm_s"] = dv_y_isop.cumsum() * 100

    vel_cols = ["depth_m"] + [col for col in depth_df.columns if "_cm_s" in col]
    cols_to_drop = [col for col in vel_cols if col != "depth_m" and col in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    final_df = pd.merge(df, depth_df[vel_cols], on="depth_m", how="left")

    with open(file_path, "w", encoding="utf-8") as f_out:
        for line in header_lines:
            f_out.write(line)
            
    final_df.to_csv(file_path, mode="a", index=False)

    return final_df