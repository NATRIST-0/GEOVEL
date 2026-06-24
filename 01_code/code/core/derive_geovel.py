import numpy as np
import pandas as pd
from pathlib import Path

def derive_geostrophic_velocity(
    file_path: Path, level_of_no_motion: float
) -> pd.DataFrame:
    """
    Computes the geostrophic velocity profiles relative to a specified level of no motion.

    Arguments:
    - file_path: Path to the CSV file containing CTD data with plane equations coefs.
    - level_of_no_motion: Depth level (in meters) where the velocity is assumed to be zero.

    Returns:
    - DataFrame containing the derived geostrophic velocity profiles.
    """

    # Read the raw file to extract metadata header and keep it for saving later
    header_lines = []
    latitudes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                header_lines.append(line)
                # Extract latitude from the metadata lines
                if "Lat=" in line:
                    try:
                        lat_str = line.split("Lat=")[1].split(",")[0]
                        latitudes.append(float(lat_str))
                    except (IndexError, ValueError):
                        pass
            else:
                # Stop reading once we hit the dataframe columns
                break
                
    if not latitudes:
        raise ValueError("Could not find latitude metadata in the file header.")
        
    # Calculate the mean latitude from the extracted header metadata
    mean_lat = np.mean(latitudes)

    # Load the dataset ignoring the commented header lines
    df = pd.read_csv(file_path, comment='#')

    # Define constants
    g = 9.81 # m/s**2
    rho_0 = 1025.0 # kg/m**3
    omega = 7.2921e-5 # rad/s

    # Calculate the Coriolis parameter based on the mean latitude of the stations
    # Left it like this in case of an use outside Banyuls
    f = 2 * omega * np.sin(np.radians(mean_lat))

    # Filter the dataframe to isolate depth and the horizontal density gradients
    cols_to_keep = ["depth_m"] + [col for col in df.columns if "dp_dx_T" in col or "dp_dy_T" in col]
    
    # Isolate a clean, single-row-per-depth dataframe to prevent cartesian explosion
    # and to ensure the dz calculation is accurate
    depth_df = df[cols_to_keep].drop_duplicates(subset=["depth_m"]).copy()
    depth_df = depth_df.sort_values("depth_m").reset_index(drop=True)

    # Find the number of triangles dynamically based on the available gradient columns
    num_triangles = len([col for col in depth_df.columns if "dp_dx_T" in col])

    for i in range(1, num_triangles + 1):
        if f"dp_dx_T{i}" not in depth_df.columns or f"dp_dy_T{i}" not in depth_df.columns:
            continue
            
        # Calculate the thermal wind coefficient
        thermal_wind_coef = g / (rho_0 * f)

        # Compute the vertical shear of geostrophic velocity safely
        dz = depth_df["depth_m"].diff().fillna(0)
        dv_x = thermal_wind_coef * depth_df[f"dp_dy_T{i}"] * dz
        dv_y = -thermal_wind_coef * depth_df[f"dp_dx_T{i}"] * dz

        # Approximate the vertical integral using a cumulative sum
        # Convertion from m/s to cm/s
        vx_cum = dv_x.cumsum() * 100
        vy_cum = dv_y.cumsum() * 100

        # Locate the closest depth index corresponding to the chosen level of no motion
        ref_idx = (depth_df["depth_m"] - level_of_no_motion).abs().idxmin()
        vx_ref = vx_cum.loc[ref_idx]
        vy_ref = vy_cum.loc[ref_idx]

        # Subtract the ref value to enforce zero velocity at the level of no motion
        depth_df[f"vx_T{i}_cm_s"] = vx_cum - vx_ref
        depth_df[f"vy_T{i}_cm_s"] = vy_cum - vy_ref

    # Gather all newly calculated velocity columns
    vel_cols = ["depth_m"] + [col for col in depth_df.columns if "_cm_s" in col]

    # Remove any previously calculated velocity columns from the main dataframe to prevent duplication
    cols_to_drop = [col for col in vel_cols if col != "depth_m" and col in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Merge the new velocity columns back into the main dataframe
    # This is now safe because depth_df strictly contains one row per depth
    final_df = pd.merge(df, depth_df[vel_cols], on="depth_m", how="left")

    # Save the updated dataframe back to the CSV while rewriting the header
    with open(file_path, "w", encoding="utf-8") as f_out:
        for line in header_lines:
            f_out.write(line)
            
    final_df.to_csv(file_path, mode="a", index=False)

    return final_df