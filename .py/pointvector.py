import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 1. Define the data mapping
# We use the corrected Longitudes (shifted to Zone 44N / Lucknow)
data = [
    {"id": "pixel_lat26.8682_lon74.9920", "lat": 26.8682, "lon": 80.9920},
    {"id": "pixel_lat26.8732_lon74.9886", "lat": 26.8732, "lon": 80.9886},
    {"id": "pixel_lat26.8652_lon74.9367", "lat": 26.8652, "lon": 80.9367},
    {"id": "pixel_lat26.8423_lon74.9242", "lat": 26.8423, "lon": 80.9242},
    {"id": "pixel_lat26.8789_lon74.9291", "lat": 26.8789, "lon": 80.9291},
    {"id": "pixel_lat26.8835_lon74.9423", "lat": 26.8835, "lon": 80.9423},
]

# 2. Create a Pandas DataFrame
df = pd.DataFrame(data)

# 3. Create Geometry (Points) from Longitude and Latitude
# Note: Point takes (x, y) which is (Longitude, Latitude)
geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]

# 4. Create a GeoDataFrame
# We explicitly set the CRS to EPSG:4326 (WGS 84 Lat/Lon)
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# 5. Save to file
output_filename = "corrected_lucknow_points.geojson"
gdf.to_file(output_filename, driver="GeoJSON")

# Optional: Save as Shapefile if preferred (requires a folder)
# gdf.to_file("corrected_lucknow_points.shp")

print(f"Success! Saved {len(gdf)} points to {output_filename}")
print(gdf.head())