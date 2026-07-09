import plotly.graph_objects as go
from plotly.subplots import make_subplots

def generate_chart(epw):
    """
    Generates a combined chart overlaying Annual Daily Precipitation (line graph)
    on top of Relative Humidity (heatmap).
    
    Args:
        epw: A parsed ladybug.epw.EPW object containing standard climate data streams.
        
    Returns:
        go.Figure: The generated Plotly figure object, ready to be rendered or passed
                   to a Dash/Streamlit frontend.
    """
    # -------------------------------------------------------------------------
    # 1. Data Extraction
    # -------------------------------------------------------------------------
    # Extract the hourly data values for relative humidity and liquid precipitation depth.
    # In ladybug EPW objects, these are typically DataCollection objects, 
    # and the 8760 hourly data points are accessible via the .values attribute.
    rh_values = epw.relative_humidity.values
    precip_values = epw.liquid_precipitation_depth.values
    
    # -------------------------------------------------------------------------
    # 2. Data Processing (Matrix Math)
    # -------------------------------------------------------------------------
    # The heatmap requires a Z-value matrix where rows correspond to the Y-axis (Hours)
    # and columns correspond to the X-axis (Days).
    # Therefore, we initialize a 24 (rows) x 365 (columns) matrix for Relative Humidity.
    rh_matrix = [[0] * 365 for _ in range(24)]
    
    # We initialize a 1D list of length 365 to store the daily sum of precipitation.
    daily_precip = [0.0] * 365
    
    # Iterate over every day (0-364) and every hour (0-23)
    for day in range(365):
        day_precip_sum = 0.0
        
        for hour in range(24):
            # Calculate the corresponding 1D index in the 8760 array
            # Day 0, Hour 0 -> index 0. Day 0, Hour 23 -> index 23.
            # Day 1, Hour 0 -> index 24.
            idx = day * 24 + hour
            
            # Populate the Relative Humidity matrix (Hour is the row, Day is the column)
            rh_matrix[hour][day] = rh_values[idx]
            
            # Accumulate the precipitation for the current day
            day_precip_sum += precip_values[idx]
            
        # Store the summed precipitation for the day
        daily_precip[day] = day_precip_sum

    # -------------------------------------------------------------------------
    # 3. Chart Generation (Base Layer & Overlay Layer)
    # -------------------------------------------------------------------------
    # Initialize a figure with a secondary Y-axis to overlay the line graph on the heatmap
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Define axes values (1-indexed for better readability on chart)
    days = list(range(1, 366))  # 1 to 365
    hours = list(range(1, 25))  # 1 to 24
    
    # Define custom colorscale mimicking the reference image:
    # Yellow (low) -> Green -> Cyan -> Blue -> Dark Blue (high)
    custom_colorscale = [
        [0.0, "yellow"],
        [0.25, "yellowgreen"],
        [0.5, "cyan"],
        [0.75, "dodgerblue"],
        [1.0, "darkblue"]
    ]
    
    # Add Base Layer (Heatmap) to the primary Y-axis
    fig.add_trace(
        go.Heatmap(
            z=rh_matrix,
            x=days,
            y=hours,
            colorscale=custom_colorscale,
            colorbar=dict(
                title="%",
                x=-0.1,  # Position the colorbar on the far left side
                xanchor="right"
            ),
            name="Relative Humidity (%)",
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>RH: %{z:.1f}%<extra></extra>"
        ),
        secondary_y=False
    )
    
    # Add Overlay Layer (Line Graph) to the secondary Y-axis
    fig.add_trace(
        go.Scatter(
            x=days,
            y=daily_precip,
            mode='lines',
            line=dict(color='white', width=1.5),  # Solid white line, no fill
            name="Daily Precipitation",
            hovertemplate="Day: %{x}<br>Precipitation: %{y:.1f} mm<extra></extra>"
        ),
        secondary_y=True
    )
    
    # -------------------------------------------------------------------------
    # 4. Formatting and Styling
    # -------------------------------------------------------------------------
    # Calculate the positions for X-axis month ticks.
    # We place the tick roughly in the middle of each month.
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    tick_vals = []
    current_day = 0
    for d in month_days:
        tick_vals.append(current_day + d / 2)  # Middle of the month
        current_day += d
        
    # Update general layout (Title, X-axis styling, margins)
    fig.update_layout(
        title="RELATIVE HUMIDITY (%) & ANNUAL DAILY PRECIPITATION",
        xaxis=dict(
            tickmode='array',
            tickvals=tick_vals,
            ticktext=month_names,
            range=[0.5, 365.5],  # Ensure the first and last heatmap columns aren't cut off
            showgrid=False
        ),
        # Increase left margin slightly to ensure the far-left colorbar isn't cropped
        margin=dict(l=100)
    )
    
    # Format Primary Y-axis (Hour, left side)
    fig.update_yaxes(
        title_text="Hour",
        range=[0.5, 24.5],  # Ensure top and bottom heatmap blocks aren't cut off
        tickmode='linear',
        tick0=2,
        dtick=2,  # Show ticks every 2 hours (2, 4, 6, ..., 24)
        secondary_y=False
    )
    
    # Format Secondary Y-axis (Precipitation, right side)
    fig.update_yaxes(
        title_text="Precipitation (mm)",
        rangemode='nonnegative',  # Ensure it scales properly starting from 0
        secondary_y=True
    )
    
    return fig
