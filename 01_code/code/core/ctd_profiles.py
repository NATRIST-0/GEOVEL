import pandas as pd
from pathlib import Path
from .utils import plot_layout


def draw_ctd_profiles(ax, file_path: Path, plot_type: str, show_avg_only: bool):
    """
    Plot CTD profiles (Temperature, Salinity or Density) as a function of depth.
    
    Arguments:
    - ax: The Matplotlib axis to draw on.
    - file_path: The path to the combined_CTD_profiles.csv file.
    - plot_type: The text selected in the UI combobox.
    - show_avg_only: Average CTD profiles data.
    """

    # Clear the existing figure to have a fresh canvas for drawing
    ax.clear()

    # Check if the data file exists and display an error message on the plot if missing
    if not Path(file_path).exists():
        print(f"No data available at {file_path}.\nPlease run data processing first.")
        return
    
    # Load the dataset
    df = pd.read_csv(file_path, comment='#')

    if "Temperature" in plot_type:
        var_col = "temperature (degC)"
        xlabel = "Temperature (°C)"
    elif "Salinity" in plot_type:
        var_col = "salinity (PSU)"
        xlabel = "Salinity (PSU)"
    elif "Density" in plot_type:
        var_col = "density (kg/m^3)"
        xlabel = "Density (kg m$^{-3}$)"
    else:
        print(f"Unknown plot type: {plot_type}")
        return

    if var_col not in df.columns or "depth_m" not in df.columns:
        print("Required data columns are missing.")
        return

    # Check if the user requested the average profile
    if show_avg_only:
        # Group data by depth levels and calculate the mean for the selected variable
        df_avg = df.groupby("depth_m")[var_col].mean().reset_index()
        
        ax.plot(df_avg[var_col], df_avg["depth_m"], label="Average Profile", color="crimson", linewidth=1.5)
    else:
        # Plot individual lines for each unique station found in the dataset
        stations = df["source_file"].unique()
        for station in stations:
            df_station = df[df["source_file"] == station]
            ax.plot(df_station[var_col], df_station["depth_m"], label=station, linewidth=1.5)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Depth (m)")
    ax.legend(loc="best")
    
    plot_layout(target=ax, layout_type="oceano", shape="square")