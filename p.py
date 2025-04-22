import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import calendar
from datetime import datetime
import os
from matplotlib.gridspec import GridSpec
from shapely.geometry import LineString

# Import the PDF extraction code we created earlier
from pdfex import main as extract_pdf_data

def create_bike_data_animation(bike_data, output_file='vancouver_bike_viz.mp4'):
    """
    Create an animated visualization of Vancouver bike data
    """
    print("Creating animation...")
    
    # Ensure data is sorted by date
    bike_data = bike_data.sort_values('Date')
    
    # Group by date and route to get monthly totals per route
    monthly_route_counts = bike_data.groupby(['Date', 'Route'])['Count'].sum().reset_index()
    
    # Get unique dates and routes
    unique_dates = sorted(bike_data['Date'].unique())
    unique_routes = sorted(bike_data['Route'].unique())
    
    # Create figure and subplots
    fig = plt.figure(figsize=(16, 10), facecolor='#f8f9fa')
    gs = GridSpec(2, 2, height_ratios=[2, 1], width_ratios=[2, 1])
    
    # Map subplot (top left)
    ax_map = fig.add_subplot(gs[0, 0])
    ax_map.set_title('Vancouver Bike Route Activity', fontsize=16)
    
    # Set up the map of Vancouver (simplified)
    ax_map.set_xlim(-123.21, -123.02)
    ax_map.set_ylim(49.24, 49.33)
    ax_map.set_xlabel('Longitude')
    ax_map.set_ylabel('Latitude')
    
    # Vancouver bike route coordinates (approximate)
    route_coords = {
        'Burrard Bridge': (-123.132, 49.276),
        'Hornby Street': (-123.123, 49.282),
        'Dunsmuir Street': (-123.115, 49.283),
        'Dunsmuir Viaduct': (-123.104, 49.278),
        'Canada Line': (-123.116, 49.262),
        'Union and Hawks': (-123.090, 49.279),
        'Lions Gate': (-123.138, 49.300),
        'Science World': (-123.103, 49.273),
        '10th and Clark': (-123.073, 49.262),
        'Point Grey Road': (-123.165, 49.272)
    }
    
    # Fill in any missing routes with random coordinates in Vancouver
    for route in unique_routes:
        if route not in route_coords:
            # Generate random coordinates within Vancouver bounds
            lon = np.random.uniform(-123.20, -123.03)
            lat = np.random.uniform(49.24, 49.32)
            route_coords[route] = (lon, lat)
    
    # Plot Vancouver shoreline (simplified)
    shoreline_x = [-123.21, -123.21, -123.19, -123.17, -123.16, -123.14, -123.12, 
                  -123.10, -123.08, -123.06, -123.04, -123.02, -123.02]
    shoreline_y = [49.29, 49.32, 49.33, 49.32, 49.29, 49.28, 49.275, 
                  49.27, 49.27, 49.26, 49.25, 49.24, 49.29]
    ax_map.plot(shoreline_x, shoreline_y, 'k-', alpha=0.5, linewidth=1)
    ax_map.fill(shoreline_x, shoreline_y, color='#e6e6e6', alpha=0.3)
    
    # Add water features
    water_color = '#a6cee3'
    # False Creek
    false_creek_x = [-123.14, -123.13, -123.12, -123.115, -123.105, -123.10, -123.12, -123.13, -123.14]
    false_creek_y = [49.27, 49.275, 49.273, 49.270, 49.268, 49.27, 49.274, 49.275, 49.27]
    ax_map.fill(false_creek_x, false_creek_y, color=water_color, alpha=0.5)
    
    # Add text labels for key areas
    ax_map.text(-123.13, 49.285, 'Downtown', fontsize=9, ha='center')
    ax_map.text(-123.16, 49.265, 'Kitsilano', fontsize=9, ha='center')
    ax_map.text(-123.07, 49.25, 'Mount Pleasant', fontsize=9, ha='center')
    
    # Time series subplot (top right)
    ax_time = fig.add_subplot(gs[0, 1])
    ax_time.set_title('Monthly Bike Count Trends', fontsize=16)
    ax_time.set_xlabel('Date')
    ax_time.set_ylabel('Total Bike Count')
    
    # Format x-axis to show years
    ax_time.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_time.xaxis.set_major_locator(mdates.YearLocator())
    
    # Bar chart subplot (bottom)
    ax_bar = fig.add_subplot(gs[1, :])
    ax_bar.set_title('Monthly Counts by Route', fontsize=16)
    ax_bar.set_xlabel('Route')
    ax_bar.set_ylabel('Bike Count')
    
    # Rotate x-axis labels for better readability
    plt.setp(ax_bar.xaxis.get_majorticklabels(), rotation=45, ha="right")
    
    # Custom colormap
    colors = [(0.0, 0.4, 0.8), (0.0, 0.7, 0.5), (0.8, 0.7, 0.0)]  # Blue -> Green -> Yellow
    cmap = LinearSegmentedColormap.from_list('vancouver_cmap', colors, N=100)
    
    # Initialize plots
    time_line, = ax_time.plot([], [], 'b-', linewidth=2)
    time_scatter = ax_time.scatter([], [], c=[], cmap=cmap, s=50, alpha=0.7)
    
    # Initialize map scatter
    map_scatter = ax_map.scatter([], [], c=[], cmap=cmap, s=[], alpha=0.7)
    
    # Add route labels
    for route, (x, y) in route_coords.items():
        ax_map.text(x, y, route, fontsize=8, ha='center', va='center', 
                   bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3'))
    
    # Initialize bar chart
    bar_container = ax_bar.bar(unique_routes, [0] * len(unique_routes), alpha=0.7)
    
    # Title with date information
    title = fig.suptitle('Vancouver Bike Counts: Loading...', fontsize=18)
    
    # Max count for consistent scaling
    max_count = monthly_route_counts['Count'].max()
    max_monthly_total = monthly_route_counts.groupby('Date')['Count'].sum().max()
    
    # Animation function
    def update(frame):
        current_date = unique_dates[frame]
        
        # Update title with current date (format: "January 2020")
        month_name = current_date.strftime('%B')
        year = current_date.year
        title.set_text(f'Vancouver Bike Counts: {month_name} {year}')
        
        # Filter data up to current date for time series
        mask = bike_data['Date'] <= current_date
        data_so_far = bike_data[mask]
        
        # Group by date for the time series
        monthly_totals = data_so_far.groupby('Date')['Count'].sum().reset_index()
        
        # Update time series line
        time_line.set_data(monthly_totals['Date'], monthly_totals['Count'])
        
        # Set time series axis limit
        if not monthly_totals.empty:
            ax_time.set_ylim(0, max_monthly_total * 1.1)
            ax_time.set_xlim(min(unique_dates), max(unique_dates))
        
        # Highlight current month in time series
        current_month_total = monthly_totals[monthly_totals['Date'] == current_date]['Count']
        if not current_month_total.empty:
            value = current_month_total.iloc[0]
            time_scatter.set_offsets(np.column_stack(([current_date], [value])))
            
            # Color based on value
            norm_value = value / max_monthly_total
            time_scatter.set_array(np.array([norm_value]))
        
        # Get route counts for current month
        current_route_counts = monthly_route_counts[monthly_route_counts['Date'] == current_date]
        
        # Update bar chart
        for i, route in enumerate(unique_routes):
            route_count = current_route_counts[current_route_counts['Route'] == route]['Count']
            if not route_count.empty:
                count = route_count.iloc[0]
            else:
                count = 0
            
            bar_container[i].set_height(count)
            
            # Set bar color based on value
            normalized_value = count / max_count if max_count > 0 else 0
            bar_container[i].set_color(cmap(normalized_value))
        
        # Set bar chart axis limit
        ax_bar.set_ylim(0, max_count * 1.1)
        
        # Update map visualization
        x_data = []
        y_data = []
        sizes = []
        colors_data = []
        
        for route in unique_routes:
            if route in route_coords:
                x, y = route_coords[route]
                x_data.append(x)
                y_data.append(y)
                
                # Get count for this route on current month
                route_count = current_route_counts[current_route_counts['Route'] == route]['Count']
                if not route_count.empty:
                    count = route_count.iloc[0]
                else:
                    count = 0
                
                # Size proportional to count
                size = 100 + (count / max_count * 1000) if max_count > 0 else 100
                sizes.append(size)
                
                # Color based on value
                norm_value = count / max_count if max_count > 0 else 0
                colors_data.append(norm_value)
        
        map_scatter.set_offsets(np.column_stack((x_data, y_data)))
        map_scatter.set_sizes(sizes)
        map_scatter.set_array(np.array(colors_data))
        
        return (title, time_line, time_scatter, map_scatter, *bar_container)
    writer = animation.FFMpegWriter(fps=5, metadata=dict(artist='Vancouver Bike Data Viz'), 
                              bitrate=1800, verbose=True)
    # Add a footer with data source information
    plt.figtext(0.5, 0.01, 'Data source: City of Vancouver Bike Counts', 
               ha='center', fontsize=10, style='italic')
    
    # Create animation
    ani = animation.FuncAnimation(
        fig, update, frames=len(unique_dates), 
        interval=200, blit=False, repeat=True
    )
    
    # Add colorbar
    cbar = fig.colorbar(map_scatter, ax=ax_map, label='Bike Count (Normalized)')
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.05)
    
    # Save animation
    writer = animation.FFMpegWriter(fps=5, metadata=dict(artist='Vancouver Bike Data Viz'), 
                                  bitrate=1800)
    ani.save(output_file, writer=writer)
    
    print(f"Animation saved as {output_file}")
    plt.close()
    
    return output_file

def main(pdf_path=None, output_file='vancouver_bike_viz.mp4'):
    """
    Main function to create visualization from PDF data
    """
    # Extract data from PDF if path is provided
    if pdf_path:
        print(f"Extracting data from {pdf_path}...")
        bike_data = extract_pdf_data(pdf_path)
    else:
        # Use sample data for demonstration if no PDF is provided
        print("No PDF path provided. Creating sample data...")
        bike_data = create_sample_data()
    
    # Create the animation
    create_bike_data_animation(bike_data, output_file)
    
    print(f"Visualization completed. Output saved to {output_file}")


if __name__ == "__main__":
    import sys
    
    # Get PDF path from command line or use default
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Get output path from command line or use default
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'vancouver_bike_viz.mp4'
    
    main(pdf_path, output_file)