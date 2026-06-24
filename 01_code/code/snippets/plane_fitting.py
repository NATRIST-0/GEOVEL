import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations # For generating all combinations of stations to form triangles

def derive_plane_equations(file_path: Path) -> pd.DataFrame:
    """
    arguments:
    - file_path: Path to the CSV file containing CTD data with density profiles.
    returns:
    - DataFrame containing the original CTD data with plane equations coefs (dp/dx, dp/dy) for each triangle of stations.
    """
    # Load the data
    df = pd.read_csv(file_path)

    # Coordinate conversion: Lat/Lon to local Cartesian meters
    lat_ref = df['latitude (deg)'].mean()
    lon_ref = df['longitude (deg)'].mean()
    lon_to_km = 111.320  # 1 degree is approx 111 km at the equator
    lat_to_km = 110.574  # 1 degree is approx 110 km

    # Create local metric X and Y coordinates (relative to the mean coordinates)
    df['x_meters'] = (df['longitude (deg)'] - lon_ref) * lon_to_km * 1000 * np.cos(np.radians(lat_ref))
    df['y_meters'] = (df['latitude (deg)'] - lat_ref) * lat_to_km * 1000

    # Identify depth cutoff and stations
    min_max_depth = df.groupby('source_file')['depth_m'].max().min()
    df_filtered = df[df['depth_m'] <= min_max_depth]

    stations = df_filtered['source_file'].unique()
    triangles = list(combinations(stations, 3))
    
    results = []

    # Calculate plane equations using the new metric coordinates
    for depth, group in df_filtered.groupby('depth_m'):
        if len(group) < 4:
            continue
            
        for i, triangle_stations in enumerate(triangles):
            triangle_data = group[group['source_file'].isin(triangle_stations)]
            
            if len(triangle_data) == 3:
                x = triangle_data['x_meters'].values
                y = triangle_data['y_meters'].values
                z = triangle_data['density (kg/m^3)'].values
                
                M = np.c_[x, y, np.ones(3)]
                
                try:
                    coeffs = np.linalg.solve(M, z)
                    results.append({
                        'depth_m': depth,
                        'triangle_id': f'T{i+1}',
                        'dp_dx': coeffs[0],  # Now in kg/m^4
                        'dp_dy': coeffs[1],  # Now in kg/m^4
                        # 'rho_1': coeffs[2]   # Base density mapped to local (0,0) meter grid
                    })
                except np.linalg.LinAlgError:
                    pass

    # Format results: pivot triangles so they become columns side-by-side
    results_df = pd.DataFrame(results)
    
    # This transforms TX into columns like drho_dx_TX, drho_dy_TX for each triangle TX
    pivot_df = results_df.pivot(index='depth_m', columns='triangle_id', values=['dp_dx', 'dp_dy'])
    
    # Flatten the multi-level columns
    pivot_df.columns = [f'{col[0]}_{col[1]}' for col in pivot_df.columns]
    pivot_df = pivot_df.reset_index()

    # Merge the new columns onto the original dataframe
    final_df = pd.merge(df, pivot_df, on='depth_m', how='left')

    # Rewrite the original file with the new metric coordinates and plane equations coeffs
    output_path = str(Path(file_path).parent / 'combined_CTD_profiles.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"File overwritten with metric coordinates and plane equations added: {output_path}")
    return final_df

# Execute
ctd_file_path = r"C:\Users\GAYRARD\Documents\GitHub\GEOVEL\02_data\combined_CTD_profiles.csv"
updated_df = derive_plane_equations(ctd_file_path)