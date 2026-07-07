import math
import plotly.graph_objects as go

def calculate_humidity_ratio(db_temp, rh, pressure):
    """
    Calculates the humidity ratio (kg water / kg dry air) 
    using the Magnus-Tetens approximation.
    
    Args:
        db_temp (float): Dry bulb temperature in Celsius.
        rh (float): Relative humidity in percentage (0-100).
        pressure (float): Atmospheric pressure in Pascals.
        
    Returns:
        float: Humidity ratio in kg/kg.
    """
    # Convert Relative Humidity from percentage to a decimal fraction
    rh_fraction = rh / 100.0
    
    # Calculate Saturation Vapor Pressure (P_ws) in Pascals using the Magnus-Tetens formula.
    # This approximation is highly accurate for typical weather temperatures (-20 C to 50 C).
    p_ws = 611.2 * math.exp((17.67 * db_temp) / (db_temp + 243.5))
    
    # Calculate Partial Pressure of Water Vapor (P_w) in Pascals
    p_w = rh_fraction * p_ws
    
    # Calculate Humidity Ratio (W) in kg water per kg dry air
    # Formula: W = 0.621945 * P_w / (P - P_w)
    humidity_ratio = 0.621945 * p_w / (pressure - p_w)
    
    return max(0.0, humidity_ratio) # Ensure it doesn't return negative values due to floating point inaccuracies

def generate_chart(epw):
    """
    Generates an interactive Psychrometric Chart using Plotly.
    Plots all 8760 hours of the year as semi-transparent scatter points
    over background curves of constant relative humidity.
    
    Args:
        epw: A parsed ladybug.epw.EPW object containing climate data.
        
    Returns:
        go.Figure: The generated Plotly figure object.
    """
    # 1. Extract necessary data from the ladybug EPW object
    # The .values property returns an iterable of the 8760 hourly data points
    db_temps = list(epw.dry_bulb_temperature.values)
    rhs = list(epw.relative_humidity.values)
    pressures = list(epw.atmospheric_station_pressure.values)
    
    # Attempt to extract the location city for the chart title, with a fallback
    location_name = epw.location.city if hasattr(epw, 'location') and hasattr(epw.location, 'city') else "Unknown Location"
    
    # 2. Compute humidity ratios for all 8760 hours
    humidity_ratios = []
    for db, rh, p in zip(db_temps, rhs, pressures):
        hr = calculate_humidity_ratio(db, rh, p)
        humidity_ratios.append(hr)
        
    # Calculate the average atmospheric pressure to draw the background relative humidity curves
    # Background curves depend on pressure; using the annual average is standard practice.
    avg_pressure = sum(pressures) / len(pressures) if pressures else 101325.0
        
    # 3. Initialize the Plotly Figure
    fig = go.Figure()
    
    # 4. Generate and plot background curves for constant relative humidity (10% to 100%)
    # We define a temperature range for these curves: from -20 to 50 degrees Celsius
    curve_temps = [-20 + i * (70.0 / 100) for i in range(101)]
    
    for rh_curve in range(10, 101, 10):
        # Calculate the humidity ratio for the curve at the given RH and average pressure
        curve_hrs = [calculate_humidity_ratio(t, rh_curve, avg_pressure) for t in curve_temps]
        
        # Emphasize the 100% RH curve (the saturation line) with a thicker, distinct color
        if rh_curve == 100:
            line_color = 'rgba(50, 150, 255, 0.8)' # Blueish saturation curve
            line_width = 2.5
        else:
            line_color = 'rgba(150, 150, 150, 0.3)' # Faded gray for other RH lines
            line_width = 1.0
            
        fig.add_trace(go.Scatter(
            x=curve_temps,
            y=curve_hrs,
            mode='lines',
            line=dict(color=line_color, width=line_width),
            name=f'{rh_curve}% RH',
            showlegend=False,
            hoverinfo='skip' # Do not show tooltips for background lines to avoid clutter
        ))
        
        # Add a text label annotation at the end of each curve (high temperature end)
        fig.add_annotation(
            x=curve_temps[-1],
            y=curve_hrs[-1],
            text=f'{rh_curve}%',
            showarrow=False,
            xanchor='left',
            yanchor='middle',
            font=dict(size=10, color='gray')
        )
        
    # 5. Plot the actual 8760 hours of EPW data as a 2D scatter plot
    # We use semi-transparent markers (opacity=0.3) so dense clusters become visually apparent
    fig.add_trace(go.Scatter(
        x=db_temps,
        y=humidity_ratios,
        mode='markers',
        marker=dict(
            size=4,
            color=db_temps,          # Map color to dry bulb temperature
            colorscale='Turbo',      # 'Turbo' is a smooth, vibrant colorscale excellent for temperatures
            opacity=0.3,             # Semi-transparent to visualize data density
            showscale=True,          # Show the color scale bar
            colorbar=dict(
                title='Temp (°C)',
                thickness=15
            )
        ),
        name='Hourly Data',
        # Format the hover text to display detailed hourly information
        text=[f'Temp: {t:.1f}°C<br>RH: {r:.1f}%<br>HR: {h:.4f} kg/kg' 
              for t, r, h in zip(db_temps, rhs, humidity_ratios)],
        hoverinfo='text'
    ))
    
    # 6. Configure the chart layout to be clean, professional, and readable
    fig.update_layout(
        title=f'Psychrometric Chart - {location_name}',
        title_font=dict(size=20, family='Arial, sans-serif'),
        xaxis_title='Dry Bulb Temperature (°C)',
        yaxis_title='Humidity Ratio (kg water / kg dry air)',
        xaxis=dict(
            range=[-20, 50],
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.5)',
            zeroline=False
        ),
        yaxis=dict(
            range=[0, 0.030],  # Y-axis limited to 30g/kg, a standard limit for Psychrometric charts
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.5)',
            zeroline=False,
            side='right'       # Conventionally, the humidity ratio axis is placed on the right
        ),
        plot_bgcolor='white',   # Clean white background
        paper_bgcolor='white',
        margin=dict(l=40, r=80, t=60, b=40),
        hovermode='closest'
    )
    
    return fig
