import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import datetime

# 1. Load Data
# Replace with your actual filename
filename = "csvs\\pixel_lat26.8732_lon74.9886.csv"

# 'comment' parameter skips the metadata lines starting with #
df = pd.read_csv(filename, comment='#')
df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

# 2. Prepare X axis (Years) for velocity calculation
start_date = df['Date'].min()
df['Days'] = (df['Date'] - start_date).dt.days
df['Years'] = df['Days'] / 365.25

x_data = df['Years'].values
y_data = df['Displacement_m'].values

# 3. Define the Piecewise Function (Two Lines)
def piecewise_linear(x, k, m1, c1, m2):
    # k: Breakpoint (in years)
    # m1, m2: Slopes (velocities)
    # c1: Intercept
    
    y = np.zeros_like(x)
    
    # Logic: line 1 before k, line 2 after k (connected)
    mask1 = x < k
    mask2 = x >= k
    
    y[mask1] = m1 * x[mask1] + c1
    
    # Ensure continuity: Line 2 starts where Line 1 ends
    y_at_k = m1 * k + c1
    y[mask2] = m2 * (x[mask2] - k) + y_at_k
    
    return y

# 4. Run the Optimizer to find the Breakpoint (k)
# Initial guesses: Break at 2.5 years, slope1=0, start=y[0], slope2=-0.1
p0 = [2.5, 0.0, y_data[0], -0.1] 

# Bounds to keep the break within the data range
bounds = (
    [x_data.min(), -np.inf, -np.inf, -np.inf],
    [x_data.max(), np.inf, np.inf, np.inf]
)

try:
    popt, _ = curve_fit(piecewise_linear, x_data, y_data, p0=p0, bounds=bounds)
    k_best, m1, c1, m2 = popt

    # 5. Interpret Results
    break_date = start_date + datetime.timedelta(days=k_best*365.25)
    v1 = m1 * 1000  # Convert m/yr to mm/yr
    v2 = m2 * 1000

    print(f"Change Point Detected: {break_date.strftime('%Y-%m-%d')}")
    print(f"Velocity 1: {v1:.2f} mm/yr")
    print(f"Velocity 2: {v2:.2f} mm/yr")

    # 6. Plotting
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Date'], y_data, color='gray', s=15, label='Original Data')

    # Create smooth line for plotting
    x_smooth = np.linspace(x_data.min(), x_data.max(), 500)
    y_smooth = piecewise_linear(x_smooth, *popt)
    dates_smooth = [start_date + datetime.timedelta(days=v*365.25) for v in x_smooth]

    plt.plot(dates_smooth, y_smooth, 'r-', linewidth=2.5, label='Best Fit (Segmented)')
    plt.axvline(break_date, color='blue', linestyle='--', label=f'Break: {break_date.strftime("%b %Y")}')
    
    plt.title(f"Piecewise Linear Fit\nBreak at {break_date.strftime('%Y-%m-%d')}")
    plt.ylabel("Displacement (m)")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Optimization failed: {e}")