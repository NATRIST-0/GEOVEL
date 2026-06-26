import numpy as np
import pandas as pd
from pathlib import Path
from .utils import plot_layout

def draw_hodograph(ax, file_path: Path, data_source: str, resolution_step: int, level_of_no_motion: float):
    """
    Draws an hodograph mapping speed and direction.
    The points are colored by depth and shifted dynamically based on the reference level.
    """
    
    fig = ax.figure
    fig.clear()
    
    if not Path(file_path).exists():
        print(f"No data available at {file_path}.\nPlease run data processing first.")
        return

    # Load the dataset ignoring the header
    df = pd.read_csv(file_path, comment='#')
    
    if not any("vx_" in col for col in df.columns):
        print("Velocity data missing.\nPlease calculate geostrophic velocities first.")
        return

    # Create a clean dataframe for plotting by removing duplicate depths
    plot_df = df.drop_duplicates(subset=["depth_m"]).sort_values("depth_m").reset_index(drop=True)
    
    # Locate the closest depth index for the level of no motion shift BEFORE applying the resolution step
    ref_idx = (plot_df["depth_m"] - level_of_no_motion).abs().idxmin()
    
    # Extract and shift the velocities based on the combobox selection
    if "Isobaric" in data_source:
        vx_col = "vx_isob_array_cm_s"
        vy_col = "vy_isob_array_cm_s"
        
        if vx_col not in plot_df.columns or vy_col not in plot_df.columns:
            print("Isobaric data is not available.")
            return
            
        # Apply dynamic shift
        vx_data = plot_df[vx_col] - plot_df[vx_col].loc[ref_idx]
        vy_data = plot_df[vy_col] - plot_df[vy_col].loc[ref_idx]
        
    elif "Isopycnal" in data_source:
        available_triangles = set(col.split("_")[2] for col in plot_df.columns if col.startswith("vx_isop_T"))
        vx_cols = [f"vx_isop_{t}_cm_s" for t in available_triangles if f"vx_isop_{t}_cm_s" in plot_df.columns]
        vy_cols = [f"vy_isop_{t}_cm_s" for t in available_triangles if f"vy_isop_{t}_cm_s" in plot_df.columns]
        
        if not vx_cols or not vy_cols:
            print("Isopycnal data is not available.")
            return
            
        # Calculate mean and apply dynamic shift
        avg_vx = plot_df[vx_cols].mean(axis=1)
        avg_vy = plot_df[vy_cols].mean(axis=1)
        
        vx_data = avg_vx - avg_vx.loc[ref_idx]
        vy_data = avg_vy - avg_vy.loc[ref_idx]
        
    else:
        print("Invalid method selected.")
        return

    # Now apply the resolution step to the shifted data and depth arrays
    vx_data = vx_data.iloc[::resolution_step].values
    vy_data = vy_data.iloc[::resolution_step].values
    depths = plot_df["depth_m"].iloc[::resolution_step].values

    # Convert Cartesian velocities to polar coordinates mapping speed to radius and direction to angle
    speed = np.sqrt(vx_data**2 + vy_data**2)
    direction = np.arctan2(vy_data, vx_data)

    # Create a polar axis to draw the true hodograph
    ax_hodo = fig.add_subplot(111, projection="polar")

    # Draw the line connecting the depth points
    ax_hodo.plot(direction, speed, color="gray", linewidth=1.0, alpha=0.6, zorder=1)

    # Draw the scatter points colored by depth
    scatter = ax_hodo.scatter(
        direction, speed, 
        c=depths, cmap="viridis_r", 
        s=30, zorder=2, edgecolor="black", linewidth=0.5
    )

    # Generate the colorbar
    cbar = fig.colorbar(scatter, ax=ax_hodo, pad=0.08)
    cbar.set_label(r"Depth (m)", rotation=270, labelpad=15)
    cbar.ax.invert_yaxis()

    # Format the polar angular ticks to display compass directions
    ax_hodo.set_xticks([0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi, 5*np.pi/4, 3*np.pi/2, 7*np.pi/4])
    ax_hodo.set_xticklabels(["E", "NE", "N", "NW", "W", "SW", "S", "SE"])
    ax_hodo.set_rlabel_position(22.5)
    
    fig.tight_layout()
    plot_layout()