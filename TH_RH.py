import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def generate_chart(epw):
    """
    Generates a Plotly Figure containing two vertically stacked hourly heatmaps:
    1. Dry Bulb Temperature
    2. Relative Humidity & Annual Daily Precipitation
    
    Args:
        epw: A parsed ladybug.epw.EPW object containing 8760 hourly weather data.
        
    Returns:
        go.Figure: The generated Plotly figure containing the two subplots.
    """
    # Extract location name
    location = epw.location.city if hasattr(epw.location, 'city') else "Unknown Location"
    
    # Extract data
    temps = epw.dry_bulb_temperature.values
    rh = epw.relative_humidity.values
    precip_values = epw.liquid_precipitation_depth.values
    
    # Reshape into (24 hours, 365 days)
    temps_matrix = np.array(temps).reshape((365, 24)).T
    rh_matrix = np.array(rh).reshape((365, 24)).T
    
    # Process precip into 365 daily totals
    daily_precip = np.array(precip_values).reshape((365, 24)).sum(axis=1)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=False, # We want x-axis labels on both
        vertical_spacing=0.15,
        specs=[
            [{"secondary_y": False}],
            [{"secondary_y": True}]
        ],
        subplot_titles=("HEATMAP", "RELATIVE HUMIDITY (%) & ANNUAL DAILY PRECIPITATION")
    )
    
    days = list(range(1, 366))
    hours = list(range(1, 25))
    
    # Custom colorscale for Temperature (Blue -> Purple -> Red -> Yellow)
    temp_colorscale = [
        [0.0, "deepskyblue"],
        [0.25, "mediumblue"],
        [0.5, "indigo"],
        [0.75, "firebrick"],
        [1.0, "gold"]
    ]
    
    # Custom colorscale for RH
    rh_colorscale = [
        [0.0, "gold"],
        [0.25, "yellowgreen"],
        [0.5, "cyan"],
        [0.75, "dodgerblue"],
        [1.0, "darkblue"]
    ]
    
    # 1. Add Temp Heatmap (row 1)
    fig.add_trace(
        go.Heatmap(
            z=temps_matrix,
            x=days,
            y=hours,
            colorscale=temp_colorscale,
            colorbar=dict(
                title="°C",
                x=-0.05,
                y=0.78,
                len=0.4,
                xanchor="right"
            ),
            name="Temperature (°C)",
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>Temp: %{z:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 2. Add RH Heatmap (row 2)
    fig.add_trace(
        go.Heatmap(
            z=rh_matrix,
            x=days,
            y=hours,
            colorscale=rh_colorscale,
            colorbar=dict(
                title="%",
                x=-0.05,
                y=0.22,
                len=0.4,
                xanchor="right"
            ),
            name="Relative Humidity (%)",
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>RH: %{z:.1f}%<extra></extra>"
        ),
        row=2, col=1, secondary_y=False
    )
    
    # 3. Add Precip Line (row 2, secondary y)
    fig.add_trace(
        go.Scatter(
            x=days,
            y=daily_precip,
            mode='lines',
            line=dict(color='white', width=1.5),
            name="Daily Precipitation",
            hovertemplate="Day: %{x}<br>Precipitation: %{y:.1f} mm<extra></extra>"
        ),
        row=2, col=1, secondary_y=True
    )
    
    # Add Toggle button for Precipitation
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        label="<b>Toggle Precipitation ⚪</b>",
                        method="restyle",
                        args=[{"visible": [True, True, True]}],
                        args2=[{"visible": [True, True, False]}]
                    )
                ]),
                showactive=False,
                x=1.0,
                xanchor="right",
                y=0.48, # Positioned above the Relative Humidity subplot
                yanchor="bottom",
                bgcolor="#4dc3c6", # Teal color similar to the gradient in the picture
                bordercolor="#4dc3c6",
                font=dict(color="white", size=12),
                pad=dict(r=10, t=5, b=5, l=10)
            )
        ]
    )
    
    # Formatting
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    tick_vals = []
    current_day = 0
    for d in month_days:
        tick_vals.append(current_day + d / 2)
        current_day += d
        
    fig.update_layout(
        autosize=True,
        margin=dict(l=100, r=50, t=80, b=50),
        plot_bgcolor='white',
        title=dict(text=f"Temperature & Humidity Heatmaps - {location}", x=0.5)
    )
    
    # Axes formatting
    # Top subplot X (Days)
    fig.update_xaxes(tickmode='array', tickvals=tick_vals, ticktext=month_names, range=[0.5, 365.5], row=1, col=1, showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1)
    # Bottom subplot X (Days)
    fig.update_xaxes(tickmode='array', tickvals=tick_vals, ticktext=month_names, range=[0.5, 365.5], row=2, col=1, showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1)
    
    # Top subplot Y (Hours)
    fig.update_yaxes(title_text="Hour", tickmode='linear', tick0=2, dtick=2, range=[0.5, 24.5], row=1, col=1, showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1)
    
    # Bottom subplot primary Y (Hours)
    fig.update_yaxes(title_text="Hour", tickmode='linear', tick0=2, dtick=2, range=[0.5, 24.5], row=2, col=1, secondary_y=False, showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1)
    
    # Bottom subplot secondary Y (Precipitation)
    fig.update_yaxes(title_text="Precipitation (mm)", rangemode='nonnegative', row=2, col=1, secondary_y=True, showgrid=False)
    
    return fig
