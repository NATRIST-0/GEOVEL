import numpy as np
import pandas as pd
from pathlib import Path
from .utils import plot_layout

def draw_hodograph(ax, file_path: Path, data_source: str, resolution_step: int):
    """
    Draws an hodograph mapping speed and direction.
    The points are colored by depth.

    Arguments:
    - ax: The Matplotlib axis provided by the UI.
    - file_path: Path to the combined_CTD_profiles.csv file.
    - data_source: String indicating which data to plot.
    - resolution_step: Integer defining the step size to skip rows and reduce visual clutter.
    """
    
    # Clear the existing figure to have a fresh canvas for drawing
    fig = ax.figure
    fig.clear()
    
    # Check if the data file exists and display an error message on the plot if missing
    if not Path(file_path).exists():
        print(f"No data available at {file_path}.\nPlease run data processing first.")
        return

    # Load the dataset containing the velocity profiles
    df = pd.read_csv(file_path, comment='#')
    
    # Verify that velocity calculations have been performed before attempting to plot
    velocity_columns_exist = any("vx_T" in col for col in df.columns)
    if not velocity_columns_exist:
        print("Velocity data missing.\nPlease calculate geostrophic velocities first.")
        return

    # Remove duplicate depths
    # Should't happen, but is a security
    plot_df = df.drop_duplicates(subset=["depth_m"]).sort_values("depth_m")
    
    # Apply the resolution step to reduce the number of plotted points
    plot_df = plot_df.iloc[::resolution_step]
    depths = plot_df["depth_m"].values
    
    # Extract the velocities based on the combobox string
    if "average" in data_source.lower():
        available_triangles = set(col.split("_")[1] for col in df.columns if col.startswith("vx_T"))
        vx_cols = [f"vx_{t}_cm_s" for t in available_triangles if f"vx_{t}_cm_s" in plot_df.columns]
        vy_cols = [f"vy_{t}_cm_s" for t in available_triangles if f"vy_{t}_cm_s" in plot_df.columns]
        
        vx_data = plot_df[vx_cols].mean(axis=1).values
        vy_data = plot_df[vy_cols].mean(axis=1).values
        plot_title = r"Average Velocity (cm s$^{-1}$)"
        
    else:
        # Extract the triangle number from the string
        triangle_num = "".join(filter(str.isdigit, data_source))
        target_triangle = f"T{triangle_num}"
        
        vx_col = f"vx_{target_triangle}_cm_s"
        vy_col = f"vy_{target_triangle}_cm_s"
        
        # If the user selected a triangle that was not generated
        if vx_col not in plot_df.columns or vy_col not in plot_df.columns:
            print(f"Data for {target_triangle} is not available. Select another option.")
            return
            
        vx_data = plot_df[vx_col].values
        vy_data = plot_df[vy_col].values
        plot_title = rf"{target_triangle} Velocity (cm s$^{{-1}}$)"

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
    ax_hodo.set_title(plot_title, pad=20)
    fig.tight_layout()
    plot_layout()
