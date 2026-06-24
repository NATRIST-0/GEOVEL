import numpy as np
import pandas as pd
from pathlib import Path
from .utils import plot_layout

def draw_geovel_profiles(ax, file_path: Path, show_avg_only: bool):
    """
    Reads the processed data and draws the geostrophic velocity profiles.

    Arguments:
    - ax: The Matplotlib axis provided by the UI.
    - file_path: Path to the combined_CTD_profiles.csv file.
    - show_avg_only: Average triangle profiles.
    """
    
    # Clear the existing figure to ensure a fresh canvas for drawing
    fig = ax.figure
    fig.clear()

    # Check if the data file exists
    if not Path(file_path).exists():
        print("No data available.\nPlease run data processing first.")
        return

    # Load the dataset containing the velocity profiles
    df = pd.read_csv(file_path, comment='#')

    # Verify that velocity calculations have been performed before attempting to plot
    velocity_columns_exist = any("vx_T" in col for col in df.columns)
    if not velocity_columns_exist:
        print("Velocity data missing.\nPlease calculate geostrophic velocities first.")
        return

    # Create two side by side subplots sharing the same vertical depth axis
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122, sharey=ax1)

    # Create a clean dataframe for plotting by removing duplicate depths
    # The original dataset contains a row for each station at each depth
    # Without this Matplotlib draws a line connecting the bottom back to the top
    plot_df = df.drop_duplicates(subset=["depth_m"]).sort_values("depth_m")

    # Dynamically find the available triangles in the dataset
    available_triangles = sorted(list(set(col.split("_")[1] for col in df.columns if col.startswith("vx_T"))))

    # Define the visual colors for the spatial triangles
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    # Handle the case where the user requested only the average velocity profiles
    if show_avg_only:
        # Collect all available velocity columns dynamically for both dimensions
        vx_cols = [f"vx_{t}_cm_s" for t in available_triangles if f"vx_{t}_cm_s" in plot_df.columns]
        vy_cols = [f"vy_{t}_cm_s" for t in available_triangles if f"vy_{t}_cm_s" in plot_df.columns]

        # Calculate the horizontal mean across the collected data columns
        avg_vx = plot_df[vx_cols].mean(axis=1)
        avg_vy = plot_df[vy_cols].mean(axis=1)

        # Plot the single computed mean profile on both subplots
        ax1.plot(avg_vx, -plot_df["depth_m"], label="Mean Velocity", color="crimson")
        ax2.plot(avg_vy, -plot_df["depth_m"], label="Mean Velocity", color="crimson")
    else:
        # Initialize memory lists to track and detect perfectly overlapping lines
        plotted_vx = []
        plotted_vy = []

        # Iterate through each dynamically found triangle to plot its velocity profiles
        for i, triangle in enumerate(available_triangles):
            # Cycle through the color list safely in case there are more triangles than colors
            color = colors[i % len(colors)]
            
            vx_col = f"vx_{triangle}_cm_s"
            vy_col = f"vy_{triangle}_cm_s"

            # Ensure the data exists for the current triangle before proceeding
            if vx_col in plot_df.columns and vy_col in plot_df.columns:
                # Temporarily replace missing values with a placeholder to allow array comparison
                current_vx = plot_df[vx_col].fillna(99999).values
                current_vy = plot_df[vy_col].fillna(99999).values

                # Check if the current profile matches any previously plotted profile
                overlap_x = any(
                    np.allclose(current_vx, prev_vx, atol=1e-5)
                    for prev_vx in plotted_vx
                )
                
                # Assign a dashed line style if an overlap is detected
                style_x = "--" if overlap_x else "-"
                
                overlap_y = any(
                    np.allclose(current_vy, prev_vy, atol=1e-5)
                    for prev_vy in plotted_vy
                )
                style_y = "--" if overlap_y else "-"

                # Draw the zonal and meridional velocity profiles with their determined styles
                ax1.plot(
                    plot_df[vx_col],
                    -plot_df["depth_m"],
                    label=fr"$v_x$ {triangle}",
                    color=color,
                    linewidth=1.5,
                    linestyle=style_x,
                )
                ax2.plot(
                    plot_df[vy_col],
                    -plot_df["depth_m"],
                    label=f"$v_y$ {triangle}",
                    color=color,
                    linewidth=1.5,
                    linestyle=style_y,
                )

                # Store the current profiles in memory for future overlap comparisons
                plotted_vx.append(current_vx)
                plotted_vy.append(current_vy)

    ax1.axvline(x=0, color="black", linewidth=1, linestyle="--")
    ax1.set_xlabel(r"Velocity $v_x$ (cm s$^{-1}$)")
    ax1.set_ylabel(r"Depth (m)")
    ax1.set_title(r"Zonal Velocity ($v_x$)", pad=15)
    ax1.legend(loc="best")

    ax2.axvline(x=0, color="black", linewidth=1, linestyle="--")
    ax2.set_xlabel(r"Velocity $v_y$ (cm s$^{-1}$)")
    ax2.set_title(r"Meridional Velocity ($v_y$)", pad=15)
    ax2.legend(loc="best")

    plot_layout(target=fig, layout_type="oceano", shape="square")