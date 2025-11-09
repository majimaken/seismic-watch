import pandas as pd
import streamlit as st
import altair as alt # Import Altair for advanced charting

# --- IMPORT MODULES ---
from modules.data_loader import load_earthquake_data
from modules.config import DISPLAY_COLS, COLUMN_LEGEND 

# --- 1. PAGE FUNCTIONS (These remain mostly the same, just cleaner imports) ---

def show_dashboard(df_earthquakes, max_mag):
    """Shows the main map dashboard and filtering interface."""
    st.title("Global Earthquake Activity (Last 24 Hours)")

    st.markdown(
    """
    This dashboard displays all recorded **global earthquake events** from the past 24 hours. \\
    You can use the sidebar navigation to switch to the **More Context** view for in-depth analysis and charting.
    """
    )
    
    # Metrics and Refresh Button Layout
    col_refresh, col_count, col_time = st.columns([1, 2, 3])

    with col_refresh:
        # Simplified refresh logic: just rerun to fetch new data based on 60s cache TTL
        if st.button("Refresh Data", help="Fetch the latest data from the USGS API (bypassing the 60s cache)."):
            st.rerun() # Will reuse cache if still valid (less than 60s)

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
    # Using LaTeX for mathematical notation
    st.text(f"Showing results with magnitude $\\ge$ {min_mag_filter}") 
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
    st.title("Understanding Patterns and Hazards")
    
    st.info("""
    **Magnitude** quantifies earthquake strength (seismic energy release). It's a logarithmic scale where each whole number up means $\\approx30\\times$ more energy. 
    - **1.0 Mag:** Very minor; often only recorded by instruments.
    - **4.0 Mag:** Light; felt by many, causes rattling, little to no damage.
    - **7.0 Mag:** Major; serious, widespread destruction.
    """)
    
    if df_earthquakes.empty:
        st.warning("No data available for analysis.")
        return

    # --- Magnitude Distribution Histogram ---
    st.subheader("1. Counting the Quakes: By Magnitude")
    st.markdown("This chart shows how many earthquakes occurred at each strength level (magnitude).")
    
    mag_hist = alt.Chart(df_earthquakes).mark_bar().encode(
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

    # --- Top Country/Region Breakdown ---
    st.subheader("2. Top Regions")
    st.markdown("A look at the top 10 countries or regions that reported the most earthquake activity.")

    country_counts = df_earthquakes['country'].value_counts().reset_index()
    country_counts.columns = ['country', 'count']
    country_counts = country_counts.head(10) # Top 10

    country_bar = alt.Chart(country_counts).mark_bar().encode(
        alt.X('count', title="Number of Earthquakes"),
        alt.Y('country', sort='-x', title="Country/Region"),
        tooltip=['country', 'count']
    ).properties(
        width='container'
    )
    st.altair_chart(country_bar, use_container_width=True)

    st.markdown("---")
    
    # --- Earthquake Depth Analysis ---
    st.subheader("3. Impact Risk: Magnitude vs. Depth")
    st.markdown("Shallow quakes are the most destructive. Depth is the key factor in surface impact.")

    depth_scale = alt.Scale(
        domain=[0, 70, 700],
        range=['red', 'yellow', 'blue'],
        type='linear'
    )

    depth_scatter = alt.Chart(df_earthquakes).mark_circle(size=60).encode(
        alt.X('magnitude', title="Magnitude"),
        alt.Y('depth', title="Depth Below Surface (km)", scale=alt.Scale(reverse=True)),
        tooltip=['magnitude', alt.Tooltip('depth', title='Depth (km)'), 'country', 'region'],
        color=alt.Color('depth', scale=depth_scale, title="Depth (km)")
    ).interactive(bind_x=False, bind_y=False).properties( 
        width='container'
    )
    st.altair_chart(depth_scatter, use_container_width=True)


# --- 4. MAIN APP LOGIC ---

# Configure page settings
st.set_page_config(layout="wide", page_title="Earthquake Live Dashboard")

# Load data once using the function from the data_loader module
df_earthquakes = load_earthquake_data()
max_mag = df_earthquakes['magnitude'].max() if not df_earthquakes.empty else 0.0

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View", ["Dashboard & Map", "More Context"])

# Route based on navigation choice
if page == "Dashboard & Map":
    show_dashboard(df_earthquakes, max_mag)
elif page == "More Context":
    show_deep_dive_analysis(df_earthquakes)