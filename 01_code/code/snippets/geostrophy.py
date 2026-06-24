import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def derive_geostrophic_velocity(file_path: Path, level_of_no_motion: float) -> pd.DataFrame:
    """
    arguments:
    - file_path: Path to the CSV file containing CTD data with plane equations coefs.
    - level_of_no_motion: Depth level (in meters) where the velocity is assumed to be zero.
    returns:
    - DataFrame containing the derived geostrophic velocity profiles.
    """
    
    # Load the dataset
    df = pd.read_csv(file_path)
    
    # Physics Constants
    g = 9.81  # Gravity (m/s^2)
    rho_0 = 1025.0  # Base density (kg/m^3) --- May need to adjust based on actual data ?
    omega = 7.2921e-5  # Earth's angular velocity (rad/s)
    
    lat_col = 'latitude (deg)'
    mean_lat = df[lat_col].mean() 
    f = 2 * omega * np.sin(np.radians(mean_lat))
    
    # Filter to relevant columns and sort all depths ascending (surface to bottom)
    cols_to_keep = ['depth_m'] + [f'dp_dx_T{i}' for i in range(1,5)] + [f'dp_dy_T{i}' for i in range(1,5)]
    available_cols = [col for col in cols_to_keep if col in df.columns]
    
    # Create a depth DataFrame for calculations
    depth_df = df[available_cols].drop_duplicates().copy()
    depth_df = depth_df.sort_values('depth_m', ascending=True)
    
    dz = 1.0  # Integrate every meter
    thermal_wind_coef = g / (rho_0 * f)
    
    # Integrate Thermal Wind Shear over the full column
    for i in range(1, 5):
        if f'dp_dx_T{i}' not in depth_df.columns:
            continue
            
        dv_x = -thermal_wind_coef * depth_df[f'dp_dy_T{i}'] * dz
        dv_y =  thermal_wind_coef * depth_df[f'dp_dx_T{i}'] * dz
        
        # Cumulative sum (relative to surface) or discretized integration
        vx_cum = dv_x.cumsum() * 100  # convert to cm/s
        vy_cum = dv_y.cumsum() * 100  # convert to cm/s
        
        # Find the cumulative value exactly at the level_of_no_motion
        # idxmin() finds the closest depth if an exact integer match isn't in the index (shouldn't be an issue)
        ref_idx = (depth_df['depth_m'] - level_of_no_motion).abs().idxmin()
        vx_ref = vx_cum.loc[ref_idx]
        vy_ref = vy_cum.loc[ref_idx]
        
        # Shift the entire profile so velocity = 0 at the reference level
        depth_df[f'vx_T{i}_cm_s'] = vx_cum - vx_ref
        depth_df[f'vy_T{i}_cm_s'] = vy_cum - vy_ref

    # Merge the results back into the primary dataframe
    vel_cols = ['depth_m'] + [col for col in depth_df.columns if '_cm_s' in col]
    
    # Drop existing velocity columns from the main df if they exist from a previous run
    # Prevents issues if the function is called multiple times with different reference levels
    cols_to_drop = [col for col in vel_cols if col != 'depth_m' and col in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        
    final_df = pd.merge(df, depth_df[vel_cols], on='depth_m', how='left')
    
    # Save back to the original CSV path
    output_path = str(Path(file_path).parent / 'combined_CTD_profiles.csv')
    final_df.to_csv(output_path, index=False)
    print(f"Velocity profiles generated. Level of no motion set at {level_of_no_motion} m.")

    # Plotting v_x and v_y profiles side-by-side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

    # --- Left Plot: v_x ---
    ax1.plot(final_df['vx_T1_cm_s'], final_df['depth_m'], label='vx_T1', color='blue')
    ax1.plot(final_df['vx_T2_cm_s'], final_df['depth_m'], label='vx_T2', color='orange')
    ax1.plot(final_df['vx_T3_cm_s'], final_df['depth_m'], label='vx_T3', color='green')
    ax1.plot(final_df['vx_T4_cm_s'], final_df['depth_m'], label='vx_T4', color='red')
    
    ax1.axvline(x=0, color='black', linewidth=1, linestyle='--') # Add a 0-line for visual reference
    ax1.set_xlabel('Velocity $v_x$ (cm/s)')
    ax1.set_ylabel('Depth (m)')
    ax1.set_title('Zonal Velocity ($v_x$)')
    ax1.invert_yaxis()
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()

    # --- Right Plot: v_y ---
    ax2.plot(final_df['vy_T1_cm_s'], final_df['depth_m'], label='vy_T1', color='blue')
    ax2.plot(final_df['vy_T2_cm_s'], final_df['depth_m'], label='vy_T2', color='orange')
    ax2.plot(final_df['vy_T3_cm_s'], final_df['depth_m'], label='vy_T3', color='green')
    ax2.plot(final_df['vy_T4_cm_s'], final_df['depth_m'], label='vy_T4', color='red')
    
    ax2.axvline(x=0, color='black', linewidth=1, linestyle='--')
    ax2.set_xlabel('Velocity $v_y$ (cm/s)')
    ax2.set_title('Meridional Velocity ($v_y$)')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()

    fig.suptitle(f'Geostrophic Velocity Profiles (No Motion Level: {level_of_no_motion} m)')
    plt.tight_layout()
    plt.show()

    return final_df

# Execute
ctd_file_path = r"C:\Users\GAYRARD\Documents\GitHub\GEOVEL\02_data\combined_CTD_profiles.csv"
df_final = derive_geostrophic_velocity(ctd_file_path, 50.0)