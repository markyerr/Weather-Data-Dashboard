"""
Wind_Data.py

A module for a climate analytics dashboard that generates 
an interactive Wind Rose and Wind Velocity bar charts using Plotly and Ladybug Tools.
It separates the data into Annual and Seasonal (Dec-Feb, Mar-May, Jun-Aug, Sep-Nov) charts.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def generate_chart(epw):
    """
    Generates interactive polar bar charts (Wind Rose) and bar charts 
    from a ladybug EPW object.

    Args:
        epw (ladybug.epw.EPW): A parsed ladybug.epw.EPW object.

    Returns:
        plotly.graph_objects.Figure: The final Plotly figure object.
    """
    # 1. Extract specific data from the EPW object
    try:
        location_name = epw.location.city
    except AttributeError:
        location_name = "Unknown Location"

    wind_speeds = epw.wind_speed.values
    wind_directions = epw.wind_direction.values

    # Generate month for each hour
    months_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # Handle leap year
    if len(wind_speeds) == 8784:
        months_days[1] = 29
        
    month_for_hour = []
    for m, h in enumerate(months_days):
        month_for_hour.extend([m + 1] * (h * 24))

    # 2. Define seasons and bins
    seasons = {
        'Annual': list(range(1, 13)),
        'Dec-Feb': [12, 1, 2],
        'Mar-May': [3, 4, 5],
        'Jun-Aug': [6, 7, 8],
        'Sep-Nov': [9, 10, 11]
    }

    dir_labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    # Define speed bins for polar (Colors matched to user request)
    polar_bins = [
        (0, 0.6, '#000080', '0-0.6 m/s'),
        (0.6, 1.2, '#0000FF', '0.6-1.2 m/s'),
        (1.2, 1.8, '#0080FF', '1.2-1.8 m/s'),
        (1.8, 2.4, '#00FFFF', '1.8-2.4 m/s'),
        (2.4, 3.0, '#80FF80', '2.4-3.0 m/s'),
        (3.0, 3.6, '#ADFF2F', '3.0-3.6 m/s'),
        (3.6, 4.2, '#FFFF00', '3.6-4.2 m/s'),
        (4.2, 4.8, '#FFBF00', '4.2-4.8 m/s'),
        (4.8, 5.4, '#FF8000', '4.8-5.4 m/s'),
        (5.4, 6.0, '#FF0000', '5.4-6.0 m/s'),
        (6.0, 100, '#800000', '>6.0 m/s')
    ]

    # Define speed bins for bar chart
    bar_bins = [
        (0, 1, '#000080', '<1'),
        (1, 2, '#00FFFF', '1.00-1.99'),
        (2, 3, '#80FF80', '2.00-2.99'),
        (3, 4, '#FFFF00', '3.00-3.99'),
        (4, 5, '#FF8000', '4.00-4.99'),
        (5, 6, '#FF0000', '5.00-5.99'),
        (6, 100, '#800000', '>=6')
    ]

    # 3. Process data for all seasons
    plot_data = []
    
    for season_name, valid_months in seasons.items():
        season_speeds = []
        season_dirs = []
        for s, d, m in zip(wind_speeds, wind_directions, month_for_hour):
            if m in valid_months:
                season_speeds.append(s)
                season_dirs.append(d)
                
        total = len(season_speeds)
        freq_polar = {i: [0] * 16 for i in range(len(polar_bins))}
        freq_bar = [0] * len(bar_bins)
        
        calm_hours = 0
        
        if total > 0:
            for s, d in zip(season_speeds, season_dirs):
                if s < 0.6:
                    calm_hours += 1
                
                dir_shifted = (d + 11.25) % 360
                dir_index = int(dir_shifted // 22.5)
                
                for i, (min_s, max_s, _, _) in enumerate(polar_bins):
                    if min_s <= s < max_s:
                        freq_polar[i][dir_index] += 1
                        break
                        
                for i, (min_s, max_s, _, _) in enumerate(bar_bins):
                    if min_s <= s < max_s:
                        freq_bar[i] += 1
                        break
                        
            for i in range(len(polar_bins)):
                freq_polar[i] = [(c / total) * 100 for c in freq_polar[i]]
            freq_bar = [(c / total) * 100 for c in freq_bar]
            
            mean_v = sum(season_speeds) / total
            min_v = min(season_speeds)
            max_v = max(season_speeds)
            sorted_s = sorted(season_speeds)
            p95_v = sorted_s[int(total * 0.95)]
            calm_pct = (calm_hours / total) * 100
        else:
            mean_v = min_v = max_v = p95_v = calm_pct = 0
            
        plot_data.append({
            'name': season_name,
            'freq_polar': freq_polar,
            'freq_bar': freq_bar,
            'mean_v': mean_v,
            'min_v': min_v,
            'max_v': max_v,
            'p95_v': p95_v,
            'calm_pct': calm_pct,
            'calm_hours': calm_hours
        })
        
    # 4. Generate subplot titles
    subplot_titles = []
    for d in plot_data:
        title_polar = f"<b>{d['name'].upper()} WIND ROSE</b><br><span style='font-size:12px'>Calm for {d['calm_pct']:.2f}% = {d['calm_hours']} hours</span>"
        title_bar = f"<b>{d['name'].upper()} WIND VELOCITY (%)</b><br><span style='font-size:12px'>Max: {d['max_v']:.1f} m/s | Min: {d['min_v']:.1f} m/s | <span style='color:red'>Mean: {d['mean_v']:.2f} m/s</span> | P95: {d['p95_v']:.1f} m/s</span>"
        subplot_titles.extend([title_polar, title_bar])

    # 5. Create figure
    fig = make_subplots(
        rows=3, cols=4,
        specs=[
            [{"type": "polar", "colspan": 2}, None, {"type": "xy", "colspan": 2}, None],
            [{"type": "polar"}, {"type": "xy"}, {"type": "polar"}, {"type": "xy"}],
            [{"type": "polar"}, {"type": "xy"}, {"type": "polar"}, {"type": "xy"}]
        ],
        subplot_titles=subplot_titles,
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    positions = [
        (1, 1, 1, 3), # Annual
        (2, 1, 2, 2), # Dec-Feb
        (2, 3, 2, 4), # Mar-May
        (3, 1, 3, 2), # Jun-Aug
        (3, 3, 3, 4)  # Sep-Nov
    ]

    for idx, d in enumerate(plot_data):
        polar_row, polar_col, bar_row, bar_col = positions[idx]
        
        # Polar traces
        for i, (min_s, max_s, color, label) in enumerate(polar_bins):
            fig.add_trace(go.Barpolar(
                r=d['freq_polar'][i],
                theta=dir_labels,
                name=label,
                marker_color=color,
                marker_line_color='white',
                marker_line_width=0.5,
                opacity=0.8,
                showlegend=(idx == 0) # Only show legend once for the first subplot
            ), row=polar_row, col=polar_col)
            
        # Bar traces
        fig.add_trace(go.Bar(
            x=[b[3] for b in bar_bins],
            y=d['freq_bar'],
            marker_color=[b[2] for b in bar_bins],
            showlegend=False,
            text=[f"{v:.1f}%" if v > 0 else "" for v in d['freq_bar']],
            textposition='auto',
            textfont=dict(size=10)
        ), row=bar_row, col=bar_col)

    # 6. Update Layouts
    fig.update_layout(
        title=dict(
            text=f"WIND ANALYSIS - {location_name.upper()}",
            font=dict(size=24, family="Arial Black"),
            x=0.5
        ),
        autosize=True,
        barmode='stack',
        template='plotly_white',
        legend=dict(
            title='Wind Speed (m/s)',
            orientation='v',
            yanchor='top',
            y=0.9,
            xanchor='right',
            x=-0.02,
            font=dict(size=10)
        ),
        margin=dict(t=120, b=50, l=150, r=50),
    )

    # We need to update ALL polar layouts
    polar_layout = dict(
        barmode='stack',
        angularaxis=dict(direction='clockwise', rotation=90, tickfont=dict(size=10)),
        radialaxis=dict(ticksuffix='%', angle=90, showticklabels=True, tickfont=dict(size=9))
    )
    
    fig.update_layout(
        polar=polar_layout,
        polar2=polar_layout,
        polar3=polar_layout,
        polar4=polar_layout,
        polar5=polar_layout
    )
    
    # Update y-axes for bar charts
    for i in range(1, 6):
        y_axis = f"yaxis{i if i > 1 else ''}"
        fig.update_layout({
            y_axis: dict(title_text="Frequency (%)", title_font=dict(size=10), tickfont=dict(size=10))
        })
        x_axis = f"xaxis{i if i > 1 else ''}"
        fig.update_layout({
            x_axis: dict(tickfont=dict(size=10))
        })

    return fig
