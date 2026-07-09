import os
import zipfile
import io
import requests
import tempfile
import streamlit as st
from ladybug.epw import EPW
import textwrap

# Import custom analytical modules
import Location
import Wind_Data
import Sunpath
import TH_RH
import Psychrometric
import Precipitation

st.set_page_config(page_title="Climate Analytics Dashboard", layout="wide")

def generate_html_dashboard(location_html, wind_fig, sunpath_fig, th_rh_fig, psych_fig, precip_fig):
    wind_html = wind_fig.to_html(full_html=False, include_plotlyjs='cdn', default_height='100%', default_width='100%')
    sunpath_html = sunpath_fig.to_html(full_html=False, include_plotlyjs=False, default_height='100%', default_width='100%')
    th_rh_html = th_rh_fig.to_html(full_html=False, include_plotlyjs=False, default_height='100%', default_width='100%')
    psych_html = psych_fig.to_html(full_html=False, include_plotlyjs=False, default_height='100%', default_width='100%')
    precip_html = precip_fig.to_html(full_html=False, include_plotlyjs=False, default_height='100%', default_width='100%')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Climate Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f4f6f9; padding-bottom: 3rem; font-family: system-ui, -apple-system, sans-serif; }}
        .dashboard-header {{ margin-top: 2rem; margin-bottom: 2rem; text-align: center; font-weight: 700; color: #2c3e50; }}
        .card {{ margin-bottom: 1.5rem; border: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .card-header {{ font-weight: 600; background-color: #ffffff; border-bottom: 1px solid #edf2f7; padding: 1rem 1.25rem; font-size: 1.1rem; color: #34495e; }}
        .card-body {{ padding: 1.5rem; aspect-ratio: 16 / 9; overflow: hidden; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="dashboard-header">Climate Analytics Dashboard</h1>
        <div class="card"><div class="card-header">Location Summary</div><div class="card-body">{location_html}</div></div>
        <div class="row"><div class="col-12"><div class="card"><div class="card-header">Wind Rose Analysis</div><div class="card-body">{wind_html}</div></div></div></div>
        <div class="row"><div class="col-12"><div class="card"><div class="card-header">Sunpath Diagram</div><div class="card-body">{sunpath_html}</div></div></div></div>
        <div class="row"><div class="col-12"><div class="card"><div class="card-header">Temperature & Humidity Heatmap</div><div class="card-body">{th_rh_html}</div></div></div></div>
        <div class="row"><div class="col-12"><div class="card"><div class="card-header">Psychrometric Analysis</div><div class="card-body">{psych_html}</div></div></div></div>
        <div class="row"><div class="col-12"><div class="card"><div class="card-header">Precipitation Analysis</div><div class="card-body">{precip_html}</div></div></div></div>
    </div>
</body>
</html>"""
    return html_content

@st.cache_data(show_spinner="Fetching and parsing EPW file...")
def fetch_and_unzip_epw(url_or_path, is_uploaded=False, uploaded_bytes=None, file_name=""):
    """
    Handles fetching and parsing an EPW weather file.
    If is_uploaded is True, we write uploaded_bytes to a temp file and parse it.
    If a zipped URL is provided, it downloads, extracts, and parses it.
    If a local zip path is provided, it extracts and parses it.
    If a local .epw path or URL is provided, it loads it.
    """
    if is_uploaded:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file_name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_bytes)
            
        if file_name.lower().endswith('.zip'):
            try:
                with zipfile.ZipFile(temp_path) as z:
                    epw_filename = next((name for name in z.namelist() if name.lower().endswith('.epw')), None)
                    if not epw_filename:
                        raise FileNotFoundError("No .epw file found inside the uploaded zip archive.")
                    z.extract(epw_filename, path=temp_dir)
                    epw_path = os.path.join(temp_dir, epw_filename)
                    return EPW(epw_path)
            except Exception as e:
                raise Exception(f"Error extracting uploaded zip file: {e}")
        else:
            return EPW(temp_path)
            
    if url_or_path.startswith(('http://', 'https://')):
        try:
            response = requests.get(url_or_path, timeout=30)
            response.raise_for_status()
            
            if url_or_path.lower().endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    epw_filename = next((name for name in z.namelist() if name.lower().endswith('.epw')), None)
                    if not epw_filename:
                        raise FileNotFoundError("No .epw file found inside the provided zip archive.")
                    
                    temp_dir = tempfile.gettempdir()
                    z.extract(epw_filename, path=temp_dir)
                    epw_path = os.path.join(temp_dir, epw_filename)
                    return EPW(epw_path)
            else:
                # Direct EPW download
                temp_dir = tempfile.gettempdir()
                epw_path = os.path.join(temp_dir, "downloaded.epw")
                with open(epw_path, "wb") as f:
                    f.write(response.content)
                return EPW(epw_path)
        except Exception as e:
            raise Exception(f"Error fetching or parsing EPW from URL: {e}")
            
    elif url_or_path.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(url_or_path) as z:
                epw_filename = next((name for name in z.namelist() if name.lower().endswith('.epw')), None)
                if not epw_filename:
                    raise FileNotFoundError("No .epw file found inside the local zip archive.")
                
                temp_dir = tempfile.gettempdir()
                z.extract(epw_filename, path=temp_dir)
                epw_path = os.path.join(temp_dir, epw_filename)
                return EPW(epw_path)
        except Exception as e:
            raise Exception(f"Error extracting local zip file: {e}")
    else:
        try:
            return EPW(url_or_path)
        except Exception as e:
            raise Exception(f"Error loading local EPW file: {e}")

def main():
    st.title("🌤️ Climate Analytics Dashboard")
    st.markdown("Upload an EPW file, provide a URL, or use the default dataset to view comprehensive climate analytics.")
    
    st.sidebar.header("Data Source")
    data_source = st.sidebar.radio(
        "Choose an option:",
        ("Use Default Data (Bangkok)", "Upload EPW or ZIP File", "Provide EPW/ZIP URL")
    )
    
    epw = None
    
    if data_source == "Use Default Data (Bangkok)":
        default_url = "THA_CRG_Bangkok.Port.484540_TMYx.zip"
        try:
            epw = fetch_and_unzip_epw(default_url)
            st.sidebar.success("Loaded Default Data")
        except Exception as e:
            st.sidebar.error(f"Failed to load default data: {e}")
            
    elif data_source == "Upload EPW or ZIP File":
        uploaded_file = st.sidebar.file_uploader("Upload .epw or .zip file", type=['epw', 'zip'])
        if uploaded_file is not None:
            try:
                # Read bytes and pass to cached function
                epw = fetch_and_unzip_epw(
                    url_or_path="",
                    is_uploaded=True, 
                    uploaded_bytes=uploaded_file.read(),
                    file_name=uploaded_file.name
                )
                st.sidebar.success("File uploaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error processing uploaded file: {e}")
                
    elif data_source == "Provide EPW/ZIP URL":
        url_input = st.sidebar.text_input("Enter URL (e.g., from EnergyPlus):")
        

        if url_input:
            try:
                epw = fetch_and_unzip_epw(url_input)
                st.sidebar.success("URL data loaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error fetching data from URL: {e}")

    if epw is not None:
        st.divider()
        
        # 1. Location Summary
        st.header("Location Summary")
        location_html = Location.get_info_table(epw)
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            st.html(textwrap.dedent(location_html))
        
        st.divider()
        
        # 2. Charts Layout
        st.subheader("Wind Rose Analysis")
        with st.spinner("Generating Wind Rose..."):
            wind_fig = Wind_Data.generate_chart(epw)
            wind_fig.update_layout(height=800)
        st.plotly_chart(wind_fig, use_container_width=True)
                
        st.divider()
        st.subheader("Sunpath Diagram")
        
        # Sunpath Settings
        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            sunpath_min = st.number_input("Min Radiation (Wh/m²)", value=0, step=100)
        with col2:
            sunpath_max = st.number_input("Max Radiation (Wh/m²)", value=1000, step=100)
            
        with st.spinner("Generating Sunpath..."):
            sunpath_fig = Sunpath.generate_chart(epw, min_rad=sunpath_min, max_rad=sunpath_max)
            sunpath_fig.update_layout(height=800)
        st.plotly_chart(sunpath_fig, use_container_width=True)
                
        st.divider()
        st.subheader("Psychrometric Analysis")
        with st.spinner("Generating Psychrometric Chart..."):
            psych_fig = Psychrometric.generate_chart(epw)
            psych_fig.update_layout(height=800)
        st.plotly_chart(psych_fig, use_container_width=True)
            
        st.divider()
        st.subheader("Temperature & Humidity Heatmap")
        with st.spinner("Generating Heatmap..."):
            th_rh_fig = TH_RH.generate_chart(epw)
            th_rh_fig.update_layout(height=900)
        st.plotly_chart(th_rh_fig, use_container_width=True)
            
        st.divider()
        st.subheader("Precipitation Analysis")
        with st.spinner("Generating Precipitation Chart..."):
            precip_fig = Precipitation.generate_chart(epw)
            precip_fig.update_layout(height=600)
        st.plotly_chart(precip_fig, use_container_width=True)
        
        # Add Export Button to Sidebar
        st.sidebar.divider()
        st.sidebar.header("Export")
        with st.spinner("Packaging Dashboard..."):
            static_html = generate_html_dashboard(location_html, wind_fig, sunpath_fig, th_rh_fig, psych_fig, precip_fig)
        st.sidebar.download_button(
            label="📦 Download Dashboard as HTML",
            data=static_html,
            file_name="climate_dashboard.html",
            mime="text/html"
        )
    else:
        if data_source == "Provide EPW/ZIP URL":
            st.info("Please provide data to view the dashboard.")
            st.markdown("### 🗺️ Find your EPW URL")
            st.markdown("Use the interactive map below to find weather data. Click on a location, copy the EPW or ZIP URL, and paste it into the sidebar.")
            import streamlit.components.v1 as components
            components.iframe("https://www.ladybug.tools/epwmap/", height=600, scrolling=True)
        elif data_source != "Use Default Data (Bangkok)":
            st.info("Please provide data to view the dashboard.")

if __name__ == "__main__":
    main()
