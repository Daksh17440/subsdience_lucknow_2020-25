# import rasterio
# from rasterio.warp import transform
# import numpy as np
# import pandas as pd

# def tif_to_csv(input_tif, output_csv):
#     """
#     Convert GeoTIFF in EPSG:32643 to CSV with EPSG:4326 coordinates
    
#     Parameters:
#     input_tif: path to input .tif file
#     output_csv: path to output .csv file
#     """
    
#     # Open the GeoTIFF
#     with rasterio.open(input_tif) as src:
#         # Read the raster data
#         data = src.read(1)  # Read first band
        
#         # Get the transformation
#         transform_matrix = src.transform
        
#         # Get all pixel coordinates
#         rows, cols = np.where(~np.isnan(data))  # Get non-NaN pixels
        
#         # Convert pixel coordinates to EPSG:32643 coordinates
#         xs, ys = rasterio.transform.xy(transform_matrix, rows, cols)
        
#         # Transform from EPSG:32643 to EPSG:4326
#         lons, lats = transform('EPSG:32643', 'EPSG:4326', xs, ys)
        
#         # Get the values at those coordinates
#         values = data[rows, cols]
        
#         # Create DataFrame
#         df = pd.DataFrame({
#             'latitude': lats,
#             'longitude': lons,
#             'value': values
#         })
        
#         # Save to CSV
#         df.to_csv(output_csv, index=False)
#         print(f"Conversion complete! Saved {len(df)} points to {output_csv}")
#         print(f"Coordinate range: Lat [{df['latitude'].min():.6f}, {df['latitude'].max():.6f}], "
#               f"Lon [{df['longitude'].min():.6f}, {df['longitude'].max():.6f}]")

# # Example usage
# if __name__ == "__main__":
#     input_file = "22_velocity.tif"
#     output_file = "22_velocity.csv"
    
#     tif_to_csv(input_file, output_file)


import rasterio
from rasterio.warp import transform
import numpy as np
import pandas as pd

def tif_to_csv(input_tif, output_csv):
    """
    Convert multi-band GeoTIFF in EPSG:32643 to CSV with EPSG:4326 coordinates
    
    Parameters:
    input_tif: path to input .tif file
    output_csv: path to output .csv file
    """
    
    # Open the GeoTIFF
    with rasterio.open(input_tif) as src:
        # Get number of bands
        n_bands = src.count
        print(f"Processing {n_bands} bands...")
        
        # Read all bands
        data = src.read()  # Shape: (bands, rows, cols)
        
        # Get the transformation
        transform_matrix = src.transform
        
        # Get band names/descriptions
        band_names = []
        for i in range(1, n_bands + 1):
            band_desc = src.descriptions[i-1]
            if band_desc:
                band_names.append(band_desc)
            else:
                band_names.append(f"band_{i}")
        
        # Get all pixel coordinates (using first band to determine valid pixels)
        rows, cols = np.where(~np.isnan(data[0]))  # Get non-NaN pixels from first band
        
        # Convert pixel coordinates to EPSG:32643 coordinates
        xs, ys = rasterio.transform.xy(transform_matrix, rows, cols)
        
        # Transform from EPSG:32643 to EPSG:4326
        lons, lats = transform('EPSG:32643', 'EPSG:4326', xs, ys)
        
        # Create DataFrame starting with coordinates
        df_data = {
            'latitude': lats,
            'longitude': lons
        }
        
        # Add all band values
        for i, band_name in enumerate(band_names):
            df_data[band_name] = data[i, rows, cols]
        
        df = pd.DataFrame(df_data)
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        print(f"Conversion complete! Saved {len(df)} points to {output_csv}")
        print(f"Bands: {', '.join(band_names)}")
        print(f"Coordinate range: Lat [{df['latitude'].min():.6f}, {df['latitude'].max():.6f}], "
              f"Lon [{df['longitude'].min():.6f}, {df['longitude'].max():.6f}]")

# Example usage
if __name__ == "__main__":
    input_file = "timeseries_georeferenced.tif"
    output_file = "timeseries_georeferenced.csv"
    
    tif_to_csv(input_file, output_file)