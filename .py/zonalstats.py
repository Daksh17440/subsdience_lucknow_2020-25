import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import numpy as np

# 1. Load Buildings
print("Loading vector file...")
vector_path = 'clipped_output.geojson'
buildings = gpd.read_file(vector_path)

# Reproject buildings to match raster EPSG (Standardize coordinates)
buildings = buildings.to_crs(epsg=32644)

# OPTIONAL: Test on just 50 buildings first to ensure it works!
# buildings = buildings.head(50) 

# 2. Load Raster into Memory (The Speed Fix)
raster_path = '20_25_velocity.tif'

print("Loading raster into RAM...")
with rasterio.open(raster_path) as src:
    # Read the data into a numpy array (Band 1)
    # This puts the whole image in RAM so we don't have to read the disk 10k times
    raster_array = src.read(1)
    raster_affine = src.transform
    raster_nodata = src.nodata
    
    # Quick check: Is the array massive?
    print(f"Raster size: {raster_array.shape}")

# 3. Run Zonal Stats using the Array (Not the file path)
print("Calculating stats (Fast Mode)...")
stats = zonal_stats(
    buildings,
    raster_array,       # Pass the numpy array
    affine=raster_affine, # Pass the geotransform
    nodata=raster_nodata, # Handle empty pixels correctly
    stats="mean",
    all_touched=True
)

# 4. Save
buildings['velocity_mean'] = [x['mean'] for x in stats]
print(f"Done! Processed {len(buildings)} buildings.")
buildings.to_file('buildings_with_velocity.geojson', driver='GeoJSON')

# import geopandas as gpd
# import rasterio
# from rasterstats import zonal_stats

# # 1. File Paths
# vector_path = 'clipped_output.geojson'
# raster_path = '20_25_velocity.tif' 

# # Check CRS (Optional, just for viewing)
# with rasterio.open(raster_path) as src:
#     print(f"Raster CRS: {src.crs}")
#     # If you want to grab the EPSG code dynamically to ensure a match:
#     raster_epsg = src.crs.to_epsg()

# # 2. Load the Buildings
# buildings = gpd.read_file(vector_path)

# # 3. FORCE the projection (Transform Vectors, NOT Raster)
# # We move the buildings to match the raster's coordinate system (EPSG:32644).
# print("Reprojecting buildings to match raster...")

# # FIX: Only apply .to_crs() to the buildings dataframe
# buildings = buildings.to_crs(epsg=32644) 
# # OR use dynamic matching: buildings = buildings.to_crs(epsg=raster_epsg)

# # 4. Double Check Overlap
# print(f"Buildings Bounds (UTM): {buildings.total_bounds}")

# # 5. Run Zonal Statistics
# print("Calculating stats...")
# stats = zonal_stats(
#     buildings,
#     raster_path, # Pass the file path string here
#     stats="mean",
#     all_touched=True 
# )

# # 6. Assign and Save
# buildings['velocity_mean'] = [x['mean'] for x in stats]

# valid_count = buildings['velocity_mean'].count()
# print(f"Success! {valid_count} buildings have velocity values.")

# buildings.to_file('buildings_with_velocity.geojson', driver='GeoJSON')