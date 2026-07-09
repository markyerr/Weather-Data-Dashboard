"""
Precipitation.py

This module contains the function to generate a monthly precipitation chart
using Plotly based on Ladybug EPW weather data.
"""

import pandas as pd
import plotly.graph_objects as go

def generate_chart(epw):
    """
    Extracts liquid precipitation depth from an EPW object, calculates monthly totals,
    and returns a Plotly go.Figure line chart with a light blue filled area.
    
    Args:
        epw (ladybug.epw.EPW): A parsed Ladybug EPW object containing weather data.
        
    Returns:
        plotly.graph_objects.Figure: The generated Plotly line chart.
    """
    
    # Extract the 8760 hourly values of liquid precipitation depth (mm)
    # The property liquid_precipitation_depth returns an hourly DataCollection
    # We use .values to get the tuple/list of the numerical data
    precip_values = epw.liquid_precipitation_depth.values
    
    # Create a Pandas date range for a standard 8760-hour (non-leap) year
    # We use 2023 as an arbitrary non-leap year to establish the 12 months correctly
    date_range = pd.date_range(start="2023-01-01 00:00", periods=8760, freq="h")
    
    # Create a DataFrame to easily group and aggregate the data
    df = pd.DataFrame({"Precipitation": precip_values}, index=date_range)
    
    # Group the hourly data by month and calculate the sum for each month
    monthly_totals = df.groupby(df.index.month).sum()
    
    # List of month names for the X-axis
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Initialize the Plotly Figure
    fig = go.Figure()
    
    # Add a scatter trace configured to look like a filled line chart
    fig.add_trace(
        go.Scatter(
            x=months,
            y=monthly_totals["Precipitation"],
            mode="lines+markers",
            name="Precipitation",
            line=dict(color="#1f77b4", width=2),     # Standard Plotly blue
            marker=dict(size=8, color="#1f77b4"),    # Markers at each data point
            fill="tozeroy",                          # Fill area down to the X-axis (Y=0)
            fillcolor="rgba(173, 216, 230, 0.4)"     # Light blue color with 40% opacity
        )
    )
    
    # Update the layout to make it clean, descriptive, and standard
    fig.update_layout(
        title="Total Monthly Precipitation",
        xaxis_title="Month",
        yaxis_title="Total Precipitation (mm)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=50, r=50, t=50, b=50) # Add some margin for clean rendering
    )
    
    # Ensure the Y-axis starts at 0 since precipitation cannot be negative
    fig.update_yaxes(rangemode="tozero")
    
    # Return the generated figure object (DO NOT use fig.show() or write to HTML)
    return fig
