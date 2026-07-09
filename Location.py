import numpy as np

def get_info_table(epw):
    """
    Extracts metadata and calculates specific climate metrics from a Ladybug EPW object.
    Returns a clean, modern HTML string formatted as a summary list or Bootstrap card body.
    
    Args:
        epw (ladybug.epw.EPW): A parsed ladybug.epw.EPW object.
        
    Returns:
        str: An HTML string containing the formatted location and climate data, 
             ready to be injected into a dashboard.
    """
    
    # --- 1. Extract Basic Metadata ---
    # We use basic try-except blocks to gracefully handle potential missing data
    try:
        loc_name = epw.location.city if hasattr(epw.location, 'city') else "Unknown Location"
        lon = epw.location.longitude if hasattr(epw.location, 'longitude') else 0.0
        lat = epw.location.latitude if hasattr(epw.location, 'latitude') else 0.0
        elevation = epw.location.elevation if hasattr(epw.location, 'elevation') else 0.0
    except Exception as e:
        loc_name, lon, lat, elevation = "Unknown Location", 0.0, 0.0, 0.0

    # --- 2. Process Hourly Data (8760 values expected) ---
    try:
        # Extract dry bulb temperatures to a NumPy array for fast calculation
        temperatures = np.array(epw.dry_bulb_temperature.values)
        
        # Calculate temperature metrics
        avg_temp = np.mean(temperatures)
        hottest_temp = np.percentile(temperatures, 99)
        coldest_temp = np.percentile(temperatures, 1)
        
        # Extract solar radiation (Values in Ladybug are typically in Wh/m2 for hourly data)
        global_rad = np.array(epw.global_horizontal_radiation.values)
        diffuse_rad = np.array(epw.diffuse_horizontal_radiation.values)
        
        # Calculate annual cumulative global horizontal radiation (convert Wh/m2 to kWh/m2)
        total_global_rad_kwh = np.sum(global_rad) / 1000.0
        
        # Calculate percentage of diffuse radiation
        total_diffuse_rad = np.sum(diffuse_rad)
        total_global_rad = np.sum(global_rad)
        
        # Safely calculate the percentage to avoid division by zero
        if total_global_rad > 0:
            diffuse_percentage = (total_diffuse_rad / total_global_rad) * 100.0
        else:
            diffuse_percentage = 0.0
            
    except Exception as e:
        # Fallbacks in case data arrays are missing or malformed
        avg_temp, hottest_temp, coldest_temp = 0.0, 0.0, 0.0
        total_global_rad_kwh, diffuse_percentage = 0.0, 0.0

    # --- 3. Köppen-Geiger / Climate Zone Estimation ---
    # Ladybug EPW objects don't always directly expose a Köppen-Geiger property, 
    # but we check for it first, then use a temperature-based estimation.
    climate_zone = "Unknown"
    
    if hasattr(epw, 'koppen_geiger_climate_zone') and epw.koppen_geiger_climate_zone:
        climate_zone = f"{epw.koppen_geiger_climate_zone}"
    elif hasattr(epw, 'location') and hasattr(epw.location, 'koppen_geiger') and epw.location.koppen_geiger:
        climate_zone = f"{epw.location.koppen_geiger}"
    else:
        # Rough estimation fallback based on average temperatures (highly simplified)
        if avg_temp >= 18:
            climate_zone = "A (Tropical) / Estimate"
        elif avg_temp < 10 and hottest_temp < 10:
            climate_zone = "E (Polar) / Estimate"
        elif coldest_temp < -3:
            climate_zone = "D (Continental) / Estimate"
        else:
            climate_zone = "C (Temperate) / Estimate"

    # --- 4. Format HTML String ---
    # Constructing a clean, modern HTML structure that mimics a Bootstrap card body.
    # We use inline styles to ensure the styling is injected reliably without external CSS.
    html_content = f"""
    <div style="font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif; color: #333; background-color: #ffffff; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 100%; border: 1px solid #eaeaea;">
        <h3 style="margin-top: 0; padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; color: #1a202c; font-size: 1.25rem; font-weight: 600;">Location Summary</h3>
        
        <div style="display: flex; flex-direction: column; gap: 0;">
            <!-- Metadata Section -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Location Name</span>
                <span style="font-weight: 600; font-size: 1rem; color: #0f172a;">{loc_name}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Coordinates</span>
                <span style="font-weight: 600; font-size: 1rem; color: #0f172a;">{lat:.4f}°, {lon:.4f}°</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Elevation</span>
                <span style="font-weight: 600; font-size: 1rem; color: #0f172a;">{elevation:.1f} m</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Köppen Climate Class.</span>
                <span style="font-weight: 600; font-size: 1rem; color: #0f172a;">{climate_zone}</span>
            </div>

            <!-- Climate Metrics Section -->
            <h4 style="margin: 20px 0 8px 0; color: #1a202c; font-size: 1.1rem; font-weight: 600;">Climate Metrics</h4>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Average Yearly Temp.</span>
                <span style="font-weight: 600; font-size: 1rem; color: #e74c3c;">{avg_temp:.1f} °C</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Hottest Temp. (99th pctl)</span>
                <span style="font-weight: 600; font-size: 1rem; color: #c0392b;">{hottest_temp:.1f} °C</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Coldest Temp. (1st pctl)</span>
                <span style="font-weight: 600; font-size: 1rem; color: #2980b9;">{coldest_temp:.1f} °C</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f4f4f4;">
                <span style="color: #64748b; font-size: 0.95rem;">Annual Horizontal Solar Radiation</span>
                <span style="font-weight: 600; font-size: 1rem; color: #f39c12;">{total_global_rad_kwh:.0f} kWh/m²</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0;">
                <span style="color: #64748b; font-size: 0.95rem;">Diffuse Solar Radiation</span>
                <span style="font-weight: 600; font-size: 1rem; color: #d35400;">{diffuse_percentage:.1f} %</span>
            </div>
        </div>
    </div>
    """
    
    return html_content
