import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ladybug.sunpath import Sunpath
from ladybug.dt import DateTime
import math

def generate_chart(epw, min_rad=0, max_rad=1000):
    """
    Generates an interactive SunPath diagram using Plotly with 3 views:
    1. Top-down Polar View (Center)
    2. South Elevation (Bottom Left)
    3. East Elevation (Bottom Right)
    """
    # 1. Extract location and radiation
    location = epw.location
    if hasattr(epw, 'global_horizontal_radiation'):
        gh_rad_collection = epw.global_horizontal_radiation
    elif hasattr(epw, 'global_horizontal_rad'):
        gh_rad_collection = epw.global_horizontal_rad
    else:
        raise AttributeError("No global horizontal radiation data.")
    
    gh_rad_values = gh_rad_collection.values
    sp = Sunpath.from_location(location)

    # 2. Bin hourly radiation data into monthly averages
    avg_rad = {m: {h: [] for h in range(24)} for m in range(1, 13)}
    
    for hoy in range(8760):
        try:
            dt = DateTime.from_hoy(hoy)
            avg_rad[dt.month][dt.hour].append(gh_rad_values[hoy])
        except:
            pass

    for m in range(1, 13):
        for h in range(24):
            if len(avg_rad[m][h]) > 0:
                avg_rad[m][h] = sum(avg_rad[m][h]) / len(avg_rad[m][h])
            else:
                avg_rad[m][h] = 0

    # 3. Calculate Daily Curves (Solstices and Equinoxes)
    daily_r, daily_theta = [], []
    daily_sx, daily_sy = [], []
    daily_ex, daily_ey = [], []
    
    months_for_curves = [12, 1, 2, 3, 4, 5, 6]
    for m in months_for_curves:
        dt_base = DateTime(m, 21, 0, 0)
        base_hoy = dt_base.hoy
        for offset in range(0, 240, 2):
            hoy = base_hoy + offset / 10.0
            if hoy >= 8760: continue
            sun = sp.calculate_sun_from_hoy(hoy)
            if sun.altitude > 0:
                azi = sun.azimuth
                alt = sun.altitude
                
                daily_r.append(90 - alt)
                daily_theta.append(azi)
                
                azi_rad = math.radians(azi)
                alt_rad = math.radians(alt)
                
                daily_sx.append(math.cos(alt_rad) * math.sin(azi_rad))
                daily_sy.append(math.sin(alt_rad))
                
                daily_ex.append(math.cos(alt_rad) * math.cos(azi_rad))
                daily_ey.append(math.sin(alt_rad))
                
        # Insert None to break line segments
        daily_r.append(None); daily_theta.append(None)
        daily_sx.append(None); daily_sy.append(None)
        daily_ex.append(None); daily_ey.append(None)

    # 4. Calculate Analemma Curves
    ana_r, ana_theta = [], []
    ana_sx, ana_sy = [], []
    ana_ex, ana_ey = [], []
    
    for h in range(24):
        has_pts = False
        for doy in range(0, 365, 5):
            hoy = doy * 24 + h
            if hoy >= 8760: continue
            sun = sp.calculate_sun_from_hoy(hoy)
            if sun.altitude > 0:
                has_pts = True
                azi = sun.azimuth
                alt = sun.altitude
                
                ana_r.append(90 - alt)
                ana_theta.append(azi)
                
                azi_rad = math.radians(azi)
                alt_rad = math.radians(alt)
                
                ana_sx.append(math.cos(alt_rad) * math.sin(azi_rad))
                ana_sy.append(math.sin(alt_rad))
                
                ana_ex.append(math.cos(alt_rad) * math.cos(azi_rad))
                ana_ey.append(math.sin(alt_rad))
        if has_pts:
            ana_r.append(None); ana_theta.append(None)
            ana_sx.append(None); ana_sy.append(None)
            ana_ex.append(None); ana_ey.append(None)

    # 5. Calculate Hourly Scatter Points
    dots_azi, dots_alt_polar = [], []
    dots_sx, dots_sy = [], []
    dots_ex, dots_ey = [], []
    dots_color, dots_text = [], []
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for m in range(1, 13):
        for h in range(24):
            dt = DateTime(m, 21, h, 0)
            if dt.hoy >= 8760: continue
            sun = sp.calculate_sun_from_hoy(dt.hoy)
            if sun.altitude > 0:
                azi = sun.azimuth
                alt = sun.altitude
                rad = avg_rad[m][h]
                
                dots_azi.append(azi)
                dots_alt_polar.append(90 - alt)
                
                azi_rad = math.radians(azi)
                alt_rad = math.radians(alt)
                
                dots_sx.append(math.cos(alt_rad) * math.sin(azi_rad))
                dots_sy.append(math.sin(alt_rad))
                
                dots_ex.append(math.cos(alt_rad) * math.cos(azi_rad))
                dots_ey.append(math.sin(alt_rad))
                
                dots_color.append(rad)
                dots_text.append(
                    f"{month_names[m-1]} 21, {h:02d}:00<br>"
                    f"Azimuth: {azi:.1f}°<br>"
                    f"Altitude: {alt:.1f}°<br>"
                    f"Avg GH Rad: {rad:.1f} Wh/m²"
                )

    # 6. Create Figure with Subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "polar", "colspan": 2}, None],
            [{"type": "xy"}, {"type": "xy"}]
        ],
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1,
        horizontal_spacing=0.05,
        subplot_titles=("", "South Elevation", "East Elevation")
    )

    line_color = 'rgba(150, 150, 150, 0.4)'
    custom_colorscale = [
        [0.0, '#4d6ba4'], [0.1, '#4d6ba4'],
        [0.1, '#97b9ee'], [0.2, '#97b9ee'],
        [0.2, '#bbd4e1'], [0.3, '#bbd4e1'],
        [0.3, '#e2eda9'], [0.4, '#e2eda9'],
        [0.4, '#faf572'], [0.5, '#faf572'],
        [0.5, '#f9ce34'], [0.6, '#f9ce34'],
        [0.6, '#f4a019'], [0.7, '#f4a019'],
        [0.7, '#ed720b'], [0.8, '#ed720b'],
        [0.8, '#ea3800'], [0.9, '#ea3800'],
        [0.9, '#e71000'], [1.0, '#e71000']
    ]
    
    # --- TOP VIEW (Polar) ---
    fig.add_trace(go.Scatterpolar(
        r=daily_r, theta=daily_theta, mode='lines',
        line=dict(color=line_color, width=1),
        hoverinfo='skip', showlegend=False
    ), row=1, col=1)
    
    fig.add_trace(go.Scatterpolar(
        r=ana_r, theta=ana_theta, mode='lines',
        line=dict(color=line_color, width=1),
        hoverinfo='skip', showlegend=False
    ), row=1, col=1)
    
    fig.add_trace(go.Scatterpolar(
        r=dots_alt_polar, theta=dots_azi, mode='markers',
        marker=dict(
            size=7, color=dots_color, colorscale=custom_colorscale,
            cmin=min_rad, cmax=max_rad,
            showscale=True,
            colorbar=dict(
                title='Wh/m²',
                x=0.02, y=0.75, len=0.45,
                tickfont=dict(size=10),
                thickness=15
            ),
            line=dict(color='black', width=0.5)
        ),
        text=dots_text, hoverinfo='text', name='Sun Position'
    ), row=1, col=1)

    # --- SOUTH ELEVATION ---
    dome_a = [math.radians(a) for a in range(181)]
    dome_x = [math.cos(a) for a in dome_a]
    dome_z = [math.sin(a) for a in dome_a]
    
    fig.add_trace(go.Scatter(x=dome_x, y=dome_z, mode='lines', line=dict(color='lightgray', width=1, dash='dash'), hoverinfo='skip', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=[-1, 1], y=[0, 0], mode='lines', line=dict(color='lightgray', width=1, dash='dash'), hoverinfo='skip', showlegend=False), row=2, col=1)
    
    fig.add_trace(go.Scatter(x=daily_sx, y=daily_sy, mode='lines', line=dict(color=line_color, width=1), hoverinfo='skip', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=ana_sx, y=ana_sy, mode='lines', line=dict(color=line_color, width=1), hoverinfo='skip', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=dots_sx, y=dots_sy, mode='markers', marker=dict(size=4.5, color=dots_color, colorscale=custom_colorscale, cmin=min_rad, cmax=max_rad, line=dict(color='black', width=0.5)), text=dots_text, hoverinfo='text', showlegend=False), row=2, col=1)

    # --- EAST ELEVATION ---
    fig.add_trace(go.Scatter(x=dome_x, y=dome_z, mode='lines', line=dict(color='lightgray', width=1, dash='dash'), hoverinfo='skip', showlegend=False), row=2, col=2)
    fig.add_trace(go.Scatter(x=[-1, 1], y=[0, 0], mode='lines', line=dict(color='lightgray', width=1, dash='dash'), hoverinfo='skip', showlegend=False), row=2, col=2)
    
    fig.add_trace(go.Scatter(x=daily_ex, y=daily_ey, mode='lines', line=dict(color=line_color, width=1), hoverinfo='skip', showlegend=False), row=2, col=2)
    fig.add_trace(go.Scatter(x=ana_ex, y=ana_ey, mode='lines', line=dict(color=line_color, width=1), hoverinfo='skip', showlegend=False), row=2, col=2)
    fig.add_trace(go.Scatter(x=dots_ex, y=dots_ey, mode='markers', marker=dict(size=4.5, color=dots_color, colorscale=custom_colorscale, cmin=min_rad, cmax=max_rad, line=dict(color='black', width=0.5)), text=dots_text, hoverinfo='text', showlegend=False), row=2, col=2)

    # --- LAYOUT UPDATES ---
    fig.update_layout(
        autosize=True,
        font=dict(family="Arial", color="black"),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 90], tickvals=[0, 15, 30, 45, 60, 75, 90], ticktext=['90°', '75°', '60°', '45°', '30°', '15°', '0°'], showline=False, gridcolor='lightgray'),
            angularaxis=dict(visible=True, direction='clockwise', rotation=90, tickvals=[0, 45, 90, 135, 180, 225, 270, 315], ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], gridcolor='lightgray'),
            bgcolor='rgba(250,250,250,0.5)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=40, b=40, l=40, r=40)
    )

    # Force subplot titles to be black
    fig.update_annotations(font=dict(color="black"))

    fig.update_xaxes(title_text="West (W) ⟶ East (E)", range=[-1.1, 1.1], showgrid=False, zeroline=False, showticklabels=False, row=2, col=1)
    fig.update_yaxes(title_text="Altitude", range=[-0.05, 1.1], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1, row=2, col=1)

    fig.update_xaxes(title_text="South (S) ⟶ North (N)", range=[-1.1, 1.1], showgrid=False, zeroline=False, showticklabels=False, row=2, col=2)
    fig.update_yaxes(title_text="", range=[-0.05, 1.1], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x2", scaleratio=1, row=2, col=2)

    return fig
