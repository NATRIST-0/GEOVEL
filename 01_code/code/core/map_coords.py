from pathlib import Path
from .utils import plot_layout

def draw_localization_plot(ax, file_path: Path):
    """
    Cleans the axes and draws a localization plot of stations relative to their barycenter.
    Reads X and Y coordinates directly from the CSV metadata header.
    """
    ax.clear()

    xy_coords = []
    
    # Read the file to extract station names, X, and Y from the header
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                # Check if the line contains our coordinate metadata
                if "Lat=" in line and "Lon=" in line and "X=" in line and "Y=" in line:
                    try:
                        # Parse the station name
                        station_name = line.split(":")[0].split(".")[0].replace("#", "").strip()
                        
                        # Parse the X and Y values
                        x_str = line.split("X=")[1].split(",")[0]
                        y_str = line.split("Y=")[1].strip()
                        
                        xy_coords.append((station_name, float(x_str), float(y_str)))
                    except (IndexError, ValueError):
                        pass
            else:
                # Stop reading once we hit the dataframe columns
                break

    # Handle missing data gracefully
    if not xy_coords:
        print("No coordinate data found.")
        return
        
    # Extract components for plotting
    xs = [c[1] for c in xy_coords]
    ys = [c[2] for c in xy_coords]
    
    # Plot stations
    ax.scatter(xs, ys, color='crimson', s=100, zorder=3, label='Stations')
    
    # Plot the barycenter (0,0)
    ax.scatter(0, 0, color='lightgray', marker='x', s=120, zorder=3, label='Barycenter')
    
    # Draw lines connecting stations in order: north -> east -> south -> west -> north
    if len(xs) >= 3:
        points = [(x, y) for x, y in zip(xs, ys)]
        north = max(points, key=lambda p: p[1])
        east = max(points, key=lambda p: p[0])
        south = min(points, key=lambda p: p[1])
        west = min(points, key=lambda p: p[0])
        ordered = [north, east, south, west, north]
        ax.plot([p[0] for p in ordered], [p[1] for p in ordered], color='#D0D0D0', linestyle='--', zorder=2)
        
    # Add text labels for each station
    for name, x, y in xy_coords:
        ax.annotate(f" {name}", (x, y), va='bottom', ha='center', xytext=(0, 4), textcoords='offset points')
        
    ax.set_xlabel("Zonal Distance X (m)")
    ax.set_ylabel("Meridional Distance Y (m)")
    ax.set_aspect('equal', adjustable='box')
    plot_layout(target=ax, shape="square", layout_type="arrow")