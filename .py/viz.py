import rasterio
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog  
import datetime
import csv                    
from rasterio.warp import transform

# ==========================================
# USER CONFIGURATION
# ==========================================

SOURCE_CRS = 'EPSG:32643'  # Update if your zone is different

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

titles = [
    "Mean Vel: 2020", "Mean Vel: 2021", "Mean Vel: 2022", "Mean Vel: 2023", "Mean Vel: 2024", "Mean Vel: 2025",
    "Mean Vel: 20-21", "Mean Vel: 22-23", "Mean Vel: 24-25",
    "Mean Vel: Overall 20-25"
]

ts_file_path = "timeseries_georeferenced.tif"

# ==========================================
# SCROLLABLE VIEWER CLASS
# ==========================================

class ScrollableInsarViewer:
    def __init__(self, root, velocity_paths, ts_path, titles):
        self.root = root
        self.root.title("InSAR Viewer")
        
        # --- NEW: Storage for the currently selected pixel data ---
        self.current_ts_data = None
        self.current_dates = None
        self.current_meta = {}  # To store coordinates
        
        # --- 1. GUI Layout ---
        # Bottom Control Panel (Button) - Packed first to stay at bottom
        self.bottom_panel = tk.Frame(root, pady=10)
        self.bottom_panel.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.save_btn = tk.Button(self.bottom_panel, text="Download Time Series (CSV)", 
                                  command=self.save_to_csv, state=tk.DISABLED,
                                  font=("Arial", 12, "bold"), bg="#dddddd")
        self.save_btn.pack()

        # Main Scrollable Area
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.canvas_widget = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas_widget.yview)
        self.scrollable_frame = tk.Frame(self.canvas_widget)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_widget.configure(scrollregion=self.canvas_widget.bbox("all"))
        )

        self.canvas_widget.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_widget.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        # --- 2. Initialize Data ---
        self.velocity_paths = velocity_paths
        self.ts_src = rasterio.open(ts_path)
        self.dates = self.extract_dates() # Load dates once
        self.ax_maps = []
        self.opened_srcs = []
        
        # --- 3. Create Figure ---
        self.fig = Figure(figsize=(14, 28), dpi=100) 
        gs = self.fig.add_gridspec(6, 2, height_ratios=[1, 1, 1, 1, 1, 1.5], hspace=0.3, wspace=0.1)

        # Plot Maps
        for i, path in enumerate(velocity_paths):
            row = i // 2
            col = i % 2
            ax = self.fig.add_subplot(gs[row, col])
            
            try:
                src = rasterio.open(path)
                self.opened_srcs.append(src)
                data = src.read(1).astype('float32')
                if src.nodata is not None:
                    data[data == src.nodata] = np.nan
                
                im = ax.imshow(data, cmap='jet_r', vmin=-0.1, vmax=0.2,
                               extent=(src.bounds.left, src.bounds.right, 
                                       src.bounds.bottom, src.bounds.top))
                
                t_str = titles[i] if i < len(titles) else f"Image {i+1}"
                ax.set_title(t_str, fontsize=12, fontweight='bold')
                ax.set_aspect('equal')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.src_ref = src
                self.ax_maps.append(ax)
            except Exception as e:
                print(f"Error loading {path}: {e}")

        cbar_ax = self.fig.add_axes([0.92, 0.45, 0.02, 0.4]) 
        self.fig.colorbar(im, cax=cbar_ax, label='Displacement (m)')

        # Plot TS placeholder
        self.ax_ts = self.fig.add_subplot(gs[5, :]) 
        self.ax_ts.set_title("Click on a map to view Time Series", fontsize=14)
        self.ax_ts.set_xlabel("Date / Band", fontsize=12)
        self.ax_ts.set_ylabel("Displacement (m)", fontsize=12)
        self.ax_ts.grid(True, linestyle='--', alpha=0.6)
        self.ax_ts.axhline(0, color='black', linewidth=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.scrollable_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
    def _on_mousewheel(self, event):
        self.canvas_widget.yview_scroll(int(-1*(event.delta/120)), "units")

    def extract_dates(self):
        try:
            descriptions = self.ts_src.descriptions
            if any(descriptions):
                return [d.strip() for d in descriptions]
            return [f"Band_{i+1}" for i in range(self.ts_src.count)]
        except:
            return None

    def on_click(self, event):
        if event.inaxes not in self.ax_maps:
            return

        ax = event.inaxes
        src = ax.src_ref
        
        try:
            x_proj, y_proj = event.xdata, event.ydata
            row, col = src.index(x_proj, y_proj)
            window = rasterio.windows.Window(col, row, 1, 1)
            ts_data = self.ts_src.read(window=window).flatten()
            
            if np.all(ts_data == self.ts_src.nodata) or np.all(np.isnan(ts_data)):
                return

            # --- Coordinate Transform ---
            try:
                lons, lats = transform(SOURCE_CRS, 'EPSG:4326', [x_proj], [y_proj])
                lon, lat = lons[0], lats[0]
                title_text = (f"Pixel: {x_proj:.2f}, {y_proj:.2f} ({SOURCE_CRS})\n"
                              f"Lat: {lat:.6f}°, Lon: {lon:.6f}°")
            except Exception:
                lon, lat = 0, 0
                title_text = f"Pixel: {x_proj:.2f}, {y_proj:.2f} (Lat/Lon Error)"

            # --- Update Plot ---
            self.ax_ts.clear()
            self.ax_ts.grid(True, linestyle='--', alpha=0.6)
            self.ax_ts.axhline(0, color='black', linewidth=0.8)
            self.ax_ts.set_title(title_text, fontsize=12, fontweight='bold')
            self.ax_ts.set_ylabel("Displacement (m)")
            
            # --- Store Data for Export ---
            self.current_ts_data = ts_data
            self.current_meta = {
                "x_proj": x_proj, "y_proj": y_proj,
                "lat": lat, "lon": lon,
                "row": row, "col": col
            }
            
            # Enable Save Button
            self.save_btn.config(state=tk.NORMAL, text=f"Download CSV (Row {row}, Col {col})")

            # Plotting logic
            if self.dates and len(self.dates) == len(ts_data):
                try:
                    # Try parsing YYYYMMDD
                    plot_dates = [datetime.datetime.strptime(d, "%Y%m%d") for d in self.dates]
                    self.ax_ts.plot(plot_dates, ts_data, '-o', color='blue', markersize=4)
                    self.current_dates = self.dates # Save string dates for CSV
                except:
                    # Fallback if dates aren't YYYYMMDD
                    self.ax_ts.plot(ts_data, '-o', color='blue')
                    self.current_dates = self.dates
            else:
                self.ax_ts.plot(ts_data, '-o', color='blue')
                self.current_dates = [f"Band_{i+1}" for i in range(len(ts_data))]

            self.canvas.draw()
            
        except Exception as e:
            print(f"Error: {e}")

    # --- NEW: CSV SAVE FUNCTION ---
    def save_to_csv(self):
        if self.current_ts_data is None:
            return
            
        # Default filename based on coordinates
        default_name = f"pixel_lat{self.current_meta['lat']:.4f}_lon{self.current_meta['lon']:.4f}.csv"
        
        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Time Series"
        )
        
        if not fpath:
            return

        try:
            with open(fpath, mode='w', newline='') as f:
                writer = csv.writer(f)
                
                # Write Metadata Header
                writer.writerow(["# InSAR Time Series Data"])
                writer.writerow(["# Source CRS", SOURCE_CRS])
                writer.writerow(["# Projected X", self.current_meta['x_proj']])
                writer.writerow(["# Projected Y", self.current_meta['y_proj']])
                writer.writerow(["# Latitude", self.current_meta['lat']])
                writer.writerow(["# Longitude", self.current_meta['lon']])
                writer.writerow(["# Raster Row", self.current_meta['row']])
                writer.writerow(["# Raster Col", self.current_meta['col']])
                writer.writerow([]) # Empty line
                
                # Write Data Columns
                writer.writerow(["Date", "Displacement_m"])
                
                for d, val in zip(self.current_dates, self.current_ts_data):
                    writer.writerow([d, val])
                    
            print(f"Saved to {fpath}")
            
        except Exception as e:
            print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed') 
    app = ScrollableInsarViewer(root, velocity_files, ts_file_path, titles)
    root.mainloop()