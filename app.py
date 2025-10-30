import requests
import pandas as pd
import streamlit as st
import numpy as np

# --- 1. DATA RETRIEVAL AND PREPARATION ---
# USGS API Endpoint: All earthquakes from the last hour
# Note: This is a low-latency, real-time data source.
# USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson" 
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson" 

@st.cache_data(ttl=60)  # Caching the data load function for 60 seconds to reduce API load
def load_earthquake_data():
    """Fetches current earthquake data from the USGS API and parses it for downstream use."""
    try:
        # Fetch data from external REST API
        response = requests.get(USGS_API_URL, timeout=10)
        # HTTP status code check is critical for pipeline robustness
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        # Critical error: API is unreachable or request timed out. Log this issue.
        st.error(f"Data retrieval error from USGS API: {e}. Returning empty DataFrame.")
        return pd.DataFrame() 

    # Extract the 'features' array, which holds the event records
    features = data.get('features', [])
    
    if not features:
        # Edge case: API call successful, but no events in the last hour.
        return pd.DataFrame()

    earthquake_list = []
    for feature in features:
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])
        
        # Data validation: Ensuring we have complete spatial data (Longitude, Latitude)
        if len(coords) >= 2:
            earthquake_list.append({
                # Geo-Data (Standardized 'lon', 'lat' for mapping)
                'lon': coords[0],            
                'lat': coords[1],            
                
                # Core Properties (Essential event metadata)
                'magnitude': props.get('mag'), 
                'place': props.get('place'),   
                # Converting Unix timestamp (ms) to pandas datetime object
                'time': pd.to_datetime(props.get('time'), unit='ms'), 
                'alert': props.get('alert'),
                
                # Additional Columns (Contextual data points for analysis)
                'felt': props.get('felt', 0),        # Number of people reporting the event
                'tsunami': props.get('tsunami', 0),  # Tsunami warning status (0/1)
                'magType': props.get('magType'),     # Type of magnitude calculation (QC measure)
                'status': props.get('status'),       # Report status (reviewed/automatic - Data Quality flag)
                'gap': props.get('gap')              # Azimuthal gap (Indicator of location uncertainty)
            })

    # Load records into a DataFrame structure for processing
    df = pd.DataFrame(earthquake_list)
    # Data Cleaning: Removing records with null values in critical geo-data columns.
    df = df.dropna(subset=['lat', 'lon', 'magnitude'])

    return df

# --- 2. STREAMLIT APPLICATION LAYOUT ---

# Load data once. Data is cached for 60 seconds to manage API usage.
df_earthquakes = load_earthquake_data()

# Page configuration for optimal dashboard viewing
st.set_page_config(layout="wide", page_title="Earthquake Live Dashboard")
st.title("🌍 Global Earthquake Activity (last 24 h)")

# Metrics and Refresh Button Layout for monitoring data freshness
col_refresh, col_count, col_time = st.columns([1, 2, 3])

with col_refresh:
    # Manual refresh allows users to bypass the cache and fetch fresh data on demand
    if st.button("Manually Refresh Data"):
        st.rerun() 

with col_count:
    st.info(f"Total Records Processed: **{len(df_earthquakes)}**")

with col_time:
    # Displaying the timestamp of the last execution/data retrieval for transparency
    st.markdown(f"**Last Data Query Time:** `{pd.Timestamp.now().strftime('%d.%m.%Y, %H:%M:%S')}`")


# --- 3. MAP VISUALIZATION ---
# Only visualize if the data pipeline returned valid records
if not df_earthquakes.empty:
    st.subheader("Geospatial Distribution of Earthquakes")
    
    # Using st.map for rapid geospatial visualization
    # 'size' is mapped to 'magnitude' to show data intensity visually.
    st.map(
        df_earthquakes, 
        latitude='lat', 
        longitude='lon', 
        size='magnitude', 
        color='#CC0000' # Highlighting seismic events with dark red
    )

    # --- 4. FILTERS AND TABLE OVERVIEW ---
    st.subheader("Key Performance Indicators (KPIs) and Data Filters")
    
    col_metric_1, col_metric_2, col_metric_3, col_metric_4 = st.columns(4)
    
    # Metrics providing real-time summary statistics of the dataset
    col_metric_1.metric("Tsunami Alert Events", df_earthquakes['tsunami'].sum())
    # Robust metric calculation: Handling potential dtype issues and empty states
    col_metric_2.metric("Max Felt Reports", int(df_earthquakes['felt'].max() if not df_earthquakes.empty and df_earthquakes['felt'].dtype != 'object' else 0))
    col_metric_3.metric("Max Magnitude Event", df_earthquakes['magnitude'].max() if not df_earthquakes.empty else 0)
    
    # Calculate average azimuthal gap (Data Quality metric)
    avg_gap = df_earthquakes['gap'].mean() if not df_earthquakes.empty else 0
    col_metric_4.metric("Average Azimuthal Gap (Quality)", f"{avg_gap:.2f}")

    st.markdown("---")
    
    # Interactive filtering mechanism for the downstream table view
    max_mag = st.slider("Filter Minimum Magnitude", 
                        min_value=0.0, 
                        max_value=float(df_earthquakes['magnitude'].max() if not df_earthquakes.empty else 5.0), 
                        value=0.0, 
                        step=0.1)
    
    # Applying the filter logic
    filtered_df = df_earthquakes[df_earthquakes['magnitude'] >= max_mag]
    
    # Display the filtered dataset, ensuring all relevant columns for analysis are present.
    st.dataframe(
        filtered_df[['time', 'place', 'magnitude', 'magType', 'felt', 'tsunami', 'alert', 'status', 'gap', 'lat', 'lon']], 
        use_container_width=True
    )

else:
    # Message indicating a pipeline failure or expected empty result set
    st.warning("No earthquake records found in the last hour or API processing failed. Check pipeline status.")