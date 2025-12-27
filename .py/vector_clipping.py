import geopandas as gpd

# 1. Load the files
input_vector = gpd.read_file('Buildings_Lucknow.geojson')
aoi_polygon = gpd.read_file('AOI.geojson')

# --- THE FIX IS HERE ---
# The AOI file claims to be 4326 (Lat/Lon) but contains UTM coordinates.
# We must OVERRIDE the metadata to tell Python: "These numbers are actually EPSG:32644"
aoi_polygon.set_crs(epsg=32644, allow_override=True, inplace=True)

# 2. NOW we can align them
# Reproject AOI to match the Input Vector (likely EPSG:4326)
# Since we fixed the label above, the conversion math will now work correctly.
if input_vector.crs != aoi_polygon.crs:
    aoi_polygon = aoi_polygon.to_crs(input_vector.crs)

# 3. Clip the data
# Using the module function gpd.clip() is often safer than the method .clip()
try:
    clipped_data = gpd.clip(input_vector, aoi_polygon)
    
    # Check if we actually got data
    if len(clipped_data) == 0:
        print("Warning: Clip result is still empty. Check if the AOI geographically covers the input data.")
    else:
        print(f"Success! Clipped {len(clipped_data)} features.")
        # 4. Save the result
        clipped_data.to_file('clipped_output.geojson', driver='GeoJSON')
        
except Exception as e:
    print(f"An error occurred during clipping: {e}")