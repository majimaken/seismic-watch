import requests
import pandas as pd
import streamlit as st
import numpy as np # Retained for potential future use, though less critical now

# --- CONFIGURATION ---
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson" 
# Note: 'map_size' is intentionally excluded here as it's only for the map visualization
DISPLAY_COLS = ['time', 'place', 'magnitude', 'magType', 'felt', 'tsunami', 'alert', 'status', 'gap', 'lat', 'lon']

# Column definitions for the legend (now in English)
COLUMN_LEGEND = {
    'time': 'Date and time of the event.',
    'place': 'Location description.',
    'magnitude': 'Strength of the earthquake (Richter scale).',
    'magType': 'Method used for magnitude calculation.',
    'felt': 'Number of user-reported perceptions.',
    'tsunami': 'Tsunami warning status (1=Yes).',
    'alert': 'USGS alert level (e.g., green, yellow).',
    'status': 'Review status (reviewed/automatic).',
    'gap': 'Largest azimuthal gap of reporting stations (data quality).',
    'lat': 'Latitude (North/South position).',
    'lon': 'Longitude (East/West position).'
}

# --- 1. DATA RETRIEVAL AND PREPARATION ---
@st.cache_data(ttl=60) 
def load_earthquake_data():
    """Fetches real-time data from the USGS API, caches it for 60 seconds, and parses it."""
    try:
        response = requests.get(USGS_API_URL, timeout=10)
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Data retrieval error from USGS API: {e}. Check your connection or API status.")
        return pd.DataFrame() 

    features = data.get('features', [])
    if not features:
        return pd.DataFrame()

    earthquake_list = []
    for feature in features:
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])
        
        # Ensure we have coordinates before proceeding
        if len(coords) >= 2:
            earthquake_list.append({
                'lon': coords[0], 
                'lat': coords[1], 
                'magnitude': props.get('mag'), 
                'place': props.get('place'), 
                'time': pd.to_datetime(props.get('time'), unit='ms'), 
                'alert': props.get('alert'),
                'felt': props.get('felt', 0), 
                'tsunami': props.get('tsunami', 0), 
                'magType': props.get('magType'), 
                'status': props.get('status'), 
                'gap': props.get('gap') 
            })

    df = pd.DataFrame(earthquake_list)
    # Final data cleaning step
    df = df.dropna(subset=['lat', 'lon', 'magnitude'])
    
    return df

# --- 2. STREAMLIT APPLICATION LAYOUT ---
st.set_page_config(layout="wide", page_title="Earthquake Live Dashboard")
st.title("🌍 Global Earthquake Activity (Last 24 Hours)")

# Load data once
df_earthquakes = load_earthquake_data()

# --- FIX for TypeError: Object of type Series is not JSON serializable ---
# Create a new column 'map_size' calculated from 'magnitude' for use in st.map()
if not df_earthquakes.empty:
    df_earthquakes['map_size'] = df_earthquakes['magnitude'].fillna(0) * 10

# Metrics and Refresh Button Layout
col_refresh, col_count, col_time = st.columns([1, 2, 3])

with col_refresh:
    if st.button("Refresh Data", help="Fetch the latest data from the USGS API (bypassing the 60s cache)."):
        st.cache_data.clear() 
        st.rerun() 

with col_count:
    st.info(f"Total Records Processed: **{len(df_earthquakes)}**")

with col_time:
    st.markdown(f"**Last Data Query Time:** `{pd.Timestamp.now().strftime('%d.%m.%Y, %H:%M:%S')}`")

# --- 3. DISPLAY & FILTERING ---
if not df_earthquakes.empty:
    
    st.subheader("Earthquake Hotspots")
    
    # Map Visualization
    # FIX APPLIED: 'size' now references the new column 'map_size' (a string) instead of a Series object
    st.map(
        df_earthquakes, 
        latitude='lat', 
        longitude='lon', 
        size='map_size', 
        color='#CC0000'
    )

    # Summary Metrics Row
    st.subheader("Summary Statistics")
    col_metric_1, col_metric_2, col_metric_3, col_metric_4 = st.columns(4)

    # Simplified metric calculations
    max_felt = df_earthquakes['felt'].max() if 'felt' in df_earthquakes.columns else 0
    max_mag = df_earthquakes['magnitude'].max() if 'magnitude' in df_earthquakes.columns else 0
    avg_gap = df_earthquakes['gap'].mean() if 'gap' in df_earthquakes.columns else 0
    
    col_metric_1.metric("Tsunami Alert Events", df_earthquakes['tsunami'].sum())
    col_metric_2.metric("Max Felt Reports", int(max_felt if pd.notna(max_felt) else 0))
    col_metric_3.metric("Max Magnitude Event", f"{max_mag:.1f}")
    col_metric_4.metric("Avg. Azimuthal Gap (Quality)", f"{avg_gap:.2f}")

    st.markdown("---")
    
    # Interactive filtering mechanism
    min_mag_filter = st.slider(
        "Show Earthquakes Stronger Than", 
        min_value=0.0, 
        max_value=float(max_mag if max_mag > 0 else 5.0), 
        value=0.0, 
        step=0.1
    )
    
    # Applying the filter logic
    filtered_df = df_earthquakes[df_earthquakes['magnitude'] >= min_mag_filter]
    
    # Metric showing filtered count
    st.metric(label="Earthquakes Matching Filter", value=f"{len(filtered_df):,}")

    st.subheader("Filtered Earthquake Data Table")
    st.text(f"Showing results with magnitude ≥ {min_mag_filter}")
    # Display the filtered dataset
    st.dataframe(
        filtered_df[DISPLAY_COLS], 
        use_container_width=True,
        hide_index=True
    )

        # UX: Legend in an Expander, displayed as a clean st.table
    with st.expander("Column Definitions"):
        st.write("This legend explains the columns displayed in the earthquake data table:")
        
        # Prepare data for the table
        legend_data = []
        for col in DISPLAY_COLS:
            legend_data.append({
                "Column Name": col,
                "Description": COLUMN_LEGEND.get(col, "No description available.")
            })
        
        legend_df = pd.DataFrame(legend_data)
        
        # Display the DataFrame as a static table for better readability
        st.table(legend_df.set_index('Column Name'))

else:
    # Message indicating a pipeline failure or expected empty result set
    st.warning("No earthquake records found in the last 24 hours or API processing failed. Please try refreshing the data.")