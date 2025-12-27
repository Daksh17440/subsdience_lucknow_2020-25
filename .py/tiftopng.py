import rasterio
import matplotlib.pyplot as plt
import numpy as np
import os

# ==========================================
# CONFIGURATION
# ==========================================

# 1. List of your velocity .tif files
velocity_files = [
    "20_velocity.tif",
    "21_velocity.tif",
    "22_velocity.tif",
    "23_velocity.tif",
    "24_velocity.tif",
    "25_velocity.tif",
    "20_21_velocity.tif",
    "22_23_velocity.tif",
    "24_25_velocity.tif",
    "20_25_velocity.tif"
]

# 2. Output folder for PNGs
output_folder = "velocity_pngs"
os.makedirs(output_folder, exist_ok=True)

# 3. Color limits (in meters)
VMIN = -0.1
VMAX = 0.1

# ==========================================
# CONVERSION LOOP
# ==========================================

print(f"Processing {len(velocity_files)} files...")

for file_path in velocity_files:
    if not os.path.exists(file_path):
        print(f"Skipping (not found): {file_path}")
        continue

    try:
        with rasterio.open(file_path) as src:
            # Read the first band
            data = src.read(1)
            
            # Mask NoData values (set them to NaN so they appear transparent/white)
            if src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)
            
            # Create a figure
            # Aspect='auto' usually fits the shape best, or use 'equal' for map accuracy
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Plot data with Reverse Jet (jet_r) and fixed limits
            im = ax.imshow(data, cmap='jet_r', vmin=VMIN, vmax=VMAX)
            
            # Add a colorbar
            cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
            cbar.set_label('Velocity (m/yr)', rotation=270, labelpad=15)
            
            # Set Title (derived from filename)
            title = os.path.splitext(file_path)[0]
            ax.set_title(title, fontsize=14, fontweight='bold')
            
            # Remove axis ticks for a cleaner map look
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Save as PNG
            output_name = f"{title}.png"
            output_path = os.path.join(output_folder, output_name)
            
            # 'bbox_inches' ensures the labels aren't cut off
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig) # Close memory
            
            print(f"Saved: {output_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print("\nAll done!")