import requests
import pandas as pd
import streamlit as st
import numpy as np 
import altair as alt # Import Altair for advanced charting

# --- CONFIGURATION ---
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson" 
# Updated DISPLAY_COLS to include 'depth'
DISPLAY_COLS = ['time', 'magnitude', 'depth', 'magType', 'region', 'country', 'felt', 'tsunami', 'alert', 'status', 'gap', 'lat', 'lon']

# Column definitions for the legend
COLUMN_LEGEND = {
    'time': 'Date and time of the event.',
    'region': 'Specific location description (distance from a local feature).', 
    'country': 'Country or major geographical region (e.g., USA, Japan, Oceanic).', 
    'magnitude': 'Strength of the earthquake (Richter scale).',
    'depth': 'Depth of the event below the surface (in km). Shallow quakes are more destructive.',
    'magType': 'Method used for magnitude calculation.',
    'felt': 'Number of user-reported perceptions.', 
    'tsunami': 'Tsunami warning status (1=Yes).', 
    'alert': 'USGS alert level (e.g., green, yellow).',
    'status': 'Review status (reviewed/automatic).', 
    'gap': 'Largest azimuthal gap of reporting stations (data quality).',
    'lat': 'Latitude (North/South position).',
    'lon': 'Longitude (East/West position).'
}

# Mapping common state/region names to their country for better grouping
COUNTRY_MAPPING = {
    # US States and Territories
    'alaska': 'USA', 'california': 'USA', 'oregon': 'USA', 'washington': 'USA', 
    'nevada': 'USA', 'puerto rico': 'USA', 'hawaii': 'USA', 'united states': 'USA',
    'oklahoma': 'USA', 'texas': 'USA', 'utah': 'USA', 'idaho': 'USA', 
    'montana': 'USA', 'wyoming': 'USA', 'colorado': 'USA', 'arizona': 'USA', 
    'new mexico': 'USA', 'kansas': 'USA', 'arkansas': 'USA', 'missouri': 'USA', 
    'illinois': 'USA', 'kentucky': 'USA', 'tennessee': 'USA', 'south carolina': 'USA', 
    'guam': 'USA', 'american samoa': 'USA', 'virgin islands': 'USA',
    'connecticut': 'USA', 'delaware': 'USA', 'florida': 'USA', 'georgia': 'USA',
    'illinois': 'USA', 'indiana': 'USA', 'iowa': 'USA', 'maine': 'USA',
    'maryland': 'USA', 'massachusetts': 'USA', 'michigan': 'USA', 'minnesota': 'USA',
    'mississippi': 'USA', 'nebraska': 'USA', 'new hampshire': 'USA', 'new jersey': 'USA',
    'new york': 'USA', 'north carolina': 'USA', 'north dakota': 'USA', 'ohio': 'USA',
    'pennsylvania': 'USA', 'rhode island': 'USA', 'south dakota': 'USA', 'vermont': 'USA',
    'virginia': 'USA', 'west virginia': 'USA', 'wisconsin': 'USA',
    
    # Other major regions
    'mexico': 'Mexico', 'japan region': 'Japan', 'indonesia region': 'Indonesia',
    'philippines region': 'Philippines', 'new zealand region': 'New Zealand',
    'canada': 'Canada', 'chile': 'Chile'
}

# Helper function to parse the place string
def parse_place(place_str):
    """Splits the USGS 'place' string into a region and a country/major area,
    and uses a mapping to resolve states/territories to their parent country."""
    if not place_str or pd.isna(place_str):
        return "Unknown Region", "Unknown Country"

    parts = place_str.split(',')
    
    if len(parts) > 1:
        # The last part is the country/major region
        country = parts[-1].strip()
        # Everything before the last comma is the region
        region = ','.join(parts[:-1]).strip()
        
        # Check for specific country mapping (e.g., converting "Alaska" to "USA")
        normalized_country = country.lower().replace(' region', '').strip()
        if normalized_country in COUNTRY_MAPPING:
            country = COUNTRY_MAPPING[normalized_country]
        
        # Fallback for edge cases like ", USA"
        if not region or region.lower() == country.lower():
            region = place_str.split(' of ')[-1].strip() if ' of ' in place_str.lower() else country
            country = "Local/Unknown"
            
    else:
        # If no comma, it's usually an oceanic or major feature.
        region = place_str.strip()
        lower_place = region.lower()
        
        # Check if the single part is a known country/region alias
        if lower_place in COUNTRY_MAPPING:
            country = COUNTRY_MAPPING[lower_place]
            region = region # Keep original string as region
        elif "ridge" in lower_place or "trench" in lower_place or "ocean" in lower_place or "sea" in lower_place or "of the earth" in lower_place:
            country = "Oceanic"
        elif "region" in lower_place or "area" in lower_place:
            # If it says 'X region' without a comma, treat it as the country name
            country = region.replace(" region", "").strip() 
        else:
            country = "Unknown/Local"
            
    return region, country


# --- 1. DATA RETRIEVAL AND PREPARATION ---
@st.cache_data(ttl=60) 
def load_earthquake_data():
    """Fetches real-time data from the USGS API, caches it, and parses the location."""
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
        
        # Ensure we have coordinates for lat/lon/depth
        if len(coords) >= 3:
            earthquake_list.append({
                'lon': coords[0], 
                'lat': coords[1], 
                'depth': coords[2], # The third coordinate is depth in km
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
        else:
            # Skip records without full coordinate data
            continue

    df = pd.DataFrame(earthquake_list)
    
    # Location Parsing
    df[['region', 'country']] = df['place'].apply(lambda x: pd.Series(parse_place(x)))
    df.drop('place', axis=1, inplace=True) 

    # Final data cleaning step and map size calculation
    df = df.dropna(subset=['lat', 'lon', 'magnitude', 'depth'])
    df['map_size'] = df['magnitude'].fillna(0) * 10
    
    return df

# --- 2. PAGE FUNCTIONS ---
# These functions act as the "pages" in the multi-page structure

def show_dashboard(df_earthquakes, max_mag):
    """Shows the main map dashboard and filtering interface."""
    st.title("Global Earthquake Activity (Last 24 Hours)")
    
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

    st.subheader("Earthquake Hotspots")
    
    # Map Visualization
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
    avg_depth = df_earthquakes['depth'].mean() if 'depth' in df_earthquakes.columns else 0
    
    col_metric_1.metric("Tsunami Alert Events", df_earthquakes['tsunami'].sum())
    col_metric_2.metric("Max Felt Reports", int(max_felt if pd.notna(max_felt) else 0))
    col_metric_3.metric("Max Magnitude Event", f"{max_mag:.1f}")
    col_metric_4.metric("Avg. Depth (km)", f"{avg_depth:.2f}")

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
    st.text(f"Showing results with magnitude $\\geq$ {min_mag_filter}")
    # Display the filtered dataset
    st.dataframe(
        filtered_df[DISPLAY_COLS], 
        use_container_width=True,
        hide_index=True
    )

    # UX: Legend in an Expander, displayed as a clean st.table
    with st.expander("Column Definitions"):
        st.write("This legend explains the columns displayed in the earthquake data table:")
        
        legend_data = []
        for col in DISPLAY_COLS:
            legend_data.append({
                "Column Name": col,
                "Description": COLUMN_LEGEND.get(col, "No description available.")
            })
        
        legend_df = pd.DataFrame(legend_data)
        st.table(legend_df.set_index('Column Name'))


def show_deep_dive_analysis(df_earthquakes):
    """Shows in-depth statistical and hazard analysis charts."""
    # Updated Main Title
    st.title("Earthquake Insights: Understanding Patterns and Hazards")
    
    if df_earthquakes.empty:
        st.warning("No data available for analysis.")
        return

    # --- Magnitude Distribution Histogram (Updated Title/Description) ---
    st.subheader("1. Counting the Quakes: By Magnitude")
    st.markdown("This chart shows how many earthquakes occurred at each strength level (magnitude). You can quickly see if there were many small tremors or fewer large ones.")
    
    # Create the Altair chart for histogram (using bins for magnitude)
    mag_hist = alt.Chart(df_earthquakes).mark_bar().encode(
        # Bin the magnitude into steps of 0.2
        alt.X("magnitude", bin=alt.Bin(step=0.2), title="Magnitude (Binned)"),
        alt.Y("count()", title="Number of Earthquakes"),
        tooltip=[
            alt.Tooltip("magnitude", bin=alt.Bin(step=0.2), title="Magnitude Range"),
            "count()"
        ]
    ).properties(
        width='container'
    )
    st.altair_chart(mag_hist, use_container_width=True)

    st.markdown("---")

    # --- Top Country/Region Breakdown (Updated Title/Description) ---
    st.subheader("2. Top Regions")
    st.markdown("A look at the top 10 countries or regions that reported the most earthquake activity in the last 24 hours.")

    # Group by country and count
    country_counts = df_earthquakes['country'].value_counts().reset_index()
    country_counts.columns = ['country', 'count']
    country_counts = country_counts.head(10) # Top 10

    # Create the Altair chart for the bar chart
    country_bar = alt.Chart(country_counts).mark_bar().encode(
        # Sort by count descending
        alt.X('count', title="Number of Earthquakes"),
        alt.Y('country', sort='-x', title="Country/Region"),
        tooltip=['country', 'count']
    ).properties(
        width='container'
    )
    st.altair_chart(country_bar, use_container_width=True)

    st.markdown("---")
    
    # --- Earthquake Depth Analysis (Updated Title/Description) ---
    st.subheader("3. Impact Risk: Magnitude vs. Depth")
    st.markdown("Shallow quakes (red dots near 0 km) are the most destructive. Depth is the key factor in damage, often outweighing magnitude for surface impact.")
    
    # Define color scale for depth (using a sequential scale where 0km is a distinct color)
    # Shallow = Red/Hazardous, Deep = Blue/Less Hazardous
    depth_scale = alt.Scale(
        domain=[0, 70, 700], 
        range=['red', 'yellow', 'blue'], 
        type='linear'
    )
    
    # Create the Altair scatter plot
    depth_scatter = alt.Chart(df_earthquakes).mark_circle(size=60).encode(
        alt.X('magnitude', title="Magnitude"),
        # Ensure depth is inverted so 0km (shallow) is at the top
        alt.Y('depth', title="Depth Below Surface (km)", scale=alt.Scale(reverse=True)),
        tooltip=['magnitude', alt.Tooltip('depth', title='Depth (km)'), 'country', 'region'],
        color=alt.Color('depth', scale=depth_scale, title="Depth (km)")
    ).interactive().properties(
        width='container'
    )
    st.altair_chart(depth_scatter, use_container_width=True)


# --- 3. MAIN APP LOGIC ---
# This section acts as the primary app.py file, controlling flow and navigation.

# Configure page settings
st.set_page_config(layout="wide", page_title="Earthquake Live Dashboard")

# Load data once
df_earthquakes = load_earthquake_data()
max_mag = df_earthquakes['magnitude'].max() if not df_earthquakes.empty else 0.0

# Sidebar Navigation (This controls which function/page is rendered)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View", ["Dashboard & Map", "More Context"])
# Route based on navigation choice
if page == "Dashboard & Map":
    show_dashboard(df_earthquakes, max_mag)
elif page == "More Context":
    show_deep_dive_analysis(df_earthquakes)