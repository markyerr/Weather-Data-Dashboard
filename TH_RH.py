import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def generate_chart(epw):
    """
    Generates a Plotly Figure containing two vertically stacked hourly heatmaps:
    1. Dry Bulb Temperature
    2. Relative Humidity
    
    Args:
        epw: A parsed ladybug.epw.EPW object containing 8760 hourly weather data.
        
    Returns:
        go.Figure: The generated Plotly figure containing the two heatmaps.
    """
    # Extract location name to use in the chart title
    location = epw.location.city if hasattr(epw.location, 'city') else "Unknown Location"
    
    # Extract the 8760 hourly values for Dry Bulb Temperature and Relative Humidity
    # Ladybug data collection objects have a .values property that returns the hourly data
    temps = epw.dry_bulb_temperature.values
    rh = epw.relative_humidity.values
    
    # EPW data is sequential (Hour 0 to 23 for Day 1, Hour 0 to 23 for Day 2, etc.)
    # We reshape the 1D list of 8760 values into a 2D array of (365 days, 24 hours).
    # Then we transpose it (.T) to get (24 hours, 365 days) so the Y-axis maps to hours and X-axis to days.
    temps_2d = np.array(temps).reshape((365, 24)).T
    rh_2d = np.array(rh).reshape((365, 24)).T
    
    # Create the axis labels
    hours = list(range(24))
    days = list(range(1, 366))
    
    # Create subplots: 2 rows, 1 column, sharing the X-axis (days of the year)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Dry Bulb Temperature (°C)", "Relative Humidity (%)")
    )
    
    # Add Temperature Heatmap to the top subplot (row 1)
    fig.add_trace(
        go.Heatmap(
            z=temps_2d,
            x=days,
            y=hours,
            colorscale='Thermal', # Appropriate color scale for temperature
            colorbar=dict(title="Temp (°C)", x=1.02, y=0.78, len=0.45),
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>Temp: %{z:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Add Relative Humidity Heatmap to the bottom subplot (row 2)
    fig.add_trace(
        go.Heatmap(
            z=rh_2d,
            x=days,
            y=hours,
            colorscale='Tealgrn', # Appropriate color scale for humidity
            colorbar=dict(title="RH (%)", x=1.02, y=0.22, len=0.45),
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>RH: %{z:.1f}%<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Update layout properties for clean aesthetics and clear axes
    fig.update_layout(
        title=f"Hourly Heatmaps of Temperature & Relative Humidity - {location}",
        title_x=0.5,
        height=800, # Taller height to accommodate two vertically stacked subplots
        yaxis=dict(
            title="Hour of Day",
            tickmode='array',
            tickvals=[0, 6, 12, 18, 23],
            ticktext=['0:00', '6:00', '12:00', '18:00', '23:00'],
            autorange='reversed' # Reversing the Y-axis so 0:00 starts at the top
        ),
        yaxis2=dict(
            title="Hour of Day",
            tickmode='array',
            tickvals=[0, 6, 12, 18, 23],
            ticktext=['0:00', '6:00', '12:00', '18:00', '23:00'],
            autorange='reversed'
        ),
        xaxis2=dict(
            title="Day of Year",
            tickmode='array',
            tickvals=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], # Approximate start of months
            ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ),
        plot_bgcolor='white'
    )
    
    # Return the generated Figure object to the calling script
    return fig
