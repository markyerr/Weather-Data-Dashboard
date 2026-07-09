import plotly.graph_objects as go
from ladybug.sunpath import Sunpath

def generate_chart(epw):
    """
    Generates an interactive SunPath diagram using Plotly.
    
    This function extracts the location and global horizontal radiation from 
    a Ladybug EPW object. It then calculates the sun's position for every hour 
    of the year and plots these positions on a polar chart, mapped with the 
    radiation data as a color scale.
    
    Args:
        epw: A parsed ladybug.epw.EPW object.
        
    Returns:
        go.Figure: The final Plotly figure object representing the SunPath.
    """
    # 1. Extract location data from the EPW object
    location = epw.location
    
    # 2. Extract global horizontal radiation data
    # Checking for both typical ladybug property and user-specified 'global_horizontal_rad'
    if hasattr(epw, 'global_horizontal_radiation'):
        gh_rad_collection = epw.global_horizontal_radiation
    elif hasattr(epw, 'global_horizontal_rad'):
        gh_rad_collection = epw.global_horizontal_rad
    else:
        raise AttributeError("The provided EPW object does not contain global horizontal radiation data.")
    
    # Extract the numerical values (list of 8760 hourly values)
    gh_rad_values = gh_rad_collection.values

    # 3. Initialize the Sunpath calculator using the EPW location
    sp = Sunpath.from_location(location)

    # Prepare lists to hold the plot data
    azimuths = []
    altitudes_inverted = []  # Plotly polar radius (center is zenith, edge is horizon)
    radiation_values = []
    hover_texts = []

    # 4. Calculate sun position for every hour of the year (0 to 8759)
    for hoy in range(8760):
        # Get the sun object for the specific hour of the year
        sun = sp.calculate_sun_from_hoy(hoy)
        
        # We only care about hours when the sun is above the horizon
        if sun.altitude > 0:
            azimuths.append(sun.azimuth)
            
            # In Plotly's polar chart, radius corresponds to distance from the center.
            # To have the horizon (0 degrees) at the edge and zenith (90 degrees) at the center:
            # radius = 90 - altitude
            altitudes_inverted.append(90 - sun.altitude)
            
            radiation = gh_rad_values[hoy]
            radiation_values.append(radiation)
            
            # Extract datetime for informative hover text
            dt = sun.datetime
            hover_text = (
                f"Date: {dt.month}/{dt.day} {dt.hour:02d}:00<br>"
                f"Azimuth: {sun.azimuth:.1f}°<br>"
                f"Altitude: {sun.altitude:.1f}°<br>"
                f"Global Horiz Rad: {radiation:.1f} Wh/m²"
            )
            hover_texts.append(hover_text)

    # 5. Create the Plotly polar scatter plot
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=altitudes_inverted,
        theta=azimuths,
        mode='markers',
        marker=dict(
            size=6,
            color=radiation_values,
            colorscale='YlOrRd',          # Warm color scale suitable for solar radiation
            showscale=True,
            colorbar=dict(
                title='Global Horiz Rad<br>(Wh/m²)',
                tickfont=dict(size=10)
            ),
            opacity=0.8,
            line=dict(width=0)
        ),
        text=hover_texts,
        hoverinfo='text',
        name='Sun Positions'
    ))

    # 6. Define the chart layout for the SunPath
    fig.update_layout(
        width=2560,
        height=1440,
        title=dict(
            text=f"Sun Path - {location.city}, {location.country}",
            font=dict(size=18, family="Arial"),
            x=0.5,
            xanchor='center'
        ),
        polar=dict(
            # Configure the radial axis (Altitude)
            radialaxis=dict(
                visible=True,
                range=[0, 90],
                # Custom ticks to show actual altitude degrees (90 at center, 0 at edge)
                tickvals=[0, 15, 30, 45, 60, 75, 90],
                ticktext=['90°', '75°', '60°', '45°', '30°', '15°', '0°'],
                title=dict(text='Altitude', font=dict(size=12)),
                showline=False,
                gridcolor='lightgray'
            ),
            # Configure the angular axis (Azimuth)
            angularaxis=dict(
                visible=True,
                direction='clockwise', # Standard for compass/sunpath directions
                rotation=90,           # Set 0 azimuth (North) to the top
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                gridcolor='lightgray'
            ),
            bgcolor='rgba(250, 250, 250, 0.9)'
        ),
        # General styling
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=80, b=40, l=40, r=40),
        showlegend=False
    )

    return fig
