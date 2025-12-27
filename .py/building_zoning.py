import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import mapclassify as mc

# --- Configuration ---
input_file = 'buildings_with_velocity.geojson'
output_png = 'building_zoning.png'
column_to_plot = 'velocity_mean'
num_zones = 5

# Define the Google Maps tile provider URL (Standard Road Map)
# You can change lyrs=m to lyrs=s (satellite) or lyrs=h (hybrid)
google_url = "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
# ---------------------

print(f"1. Loading data from {input_file}...")
buildings = gpd.read_file(input_file)

# Check data range just for info
vmin = buildings[column_to_plot].min()
vmax = buildings[column_to_plot].max()
print(f"   Data range: {vmin:.2f} to {vmax:.2f} m/yr")

# 2. Reproject to Web Mercator (EPSG:3857)
# This is crucial for alignment with Google Maps.
if buildings.crs.to_epsg() != 3857:
    print("2. Reprojecting to EPSG:3857 for web map alignment...")
    # We reproject a temporary copy for plotting so we don't alter the original data structure too much
    buildings_web = buildings.to_crs(epsg=3857)
else:
    buildings_web = buildings

# 3. Setup the Plot
print("3. Setting up the visualization...")
# Create a large figure for high resolution
fig, ax = plt.subplots(figsize=(18, 18))

# 4. Plot the Buildings
print(f"4. Zoning into {num_zones} categories and plotting (this may take a moment for 6.4 lakh buildings)...")

# We use 'jet_r'. The '_r' reverses the color ramp.
# Standard jet: Blue=Low, Red=High.
# jet_r:        Red=Low (Negative), Blue=High (Positive).
buildings_web.plot(
    column=column_to_plot,
    scheme='NaturalBreaks',   # 'NaturalBreaks' finds natural clusters in data. Alt: 'Quantiles'
    k=num_zones,              # Number of zones
    cmap='jet_r',             # Reversed jet colormap
    legend=True,
    # Legend placement options: 'lower right', 'upper left', etc.
    legend_kwds={'loc': 'lower right', 'title': 'Mean Velocity Zones (m/yr)', 'fmt': '{:.2f}'},
    alpha=0.8,                # Slight transparency to see roads beneath
    edgecolor='none',         # CRITICAL for large datasets: turn off polygon borders
    ax=ax
)

# 5. Add Google Basemap
print("5. Downloading and adding Google Basemap tiles...")
# Zoom level is tricky. 
# If it's too blurry, increase zoom (e.g., 15). If it takes forever to download, decrease it (e.g., 12).
# 'auto' usually works but sometimes picks too high a zoom for large areas. Let's try explicit first.
ctx.add_basemap(
    ax, 
    source=google_url, 
    zoom=14, 
    crs=buildings_web.crs.to_string(),
    attribution_size=8 # Make Google copyright smaller
)

# 6. Final Formatting and Saving
print("6. Finalizing image...")
ax.set_axis_off() # Remove latitude/longitude numbers
plt.title(f"Building Velocity Zones (Negative=Red/Subsidence)", fontsize=22, pad=20)

print(f"7. Saving to {output_png} (High DPI)...")
# dpi=300 ensures a high-quality print-ready PNG
plt.savefig(output_png, dpi=600, bbox_inches='tight', pad_inches=0.1)

print("Done! Visualization complete.")
# plt.show() # Uncomment if you want a popup preview before saving (slow for large data)