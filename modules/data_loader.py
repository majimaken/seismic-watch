import requests
import pandas as pd
import streamlit as st
from modules.config import USGS_API_URL, COUNTRY_MAPPING

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
            continue

    df = pd.DataFrame(earthquake_list)
    
    # Location Parsing
    df[['region', 'country']] = df['place'].apply(lambda x: pd.Series(parse_place(x)))
    df.drop('place', axis=1, inplace=True)

    # Final data cleaning step and map size calculation
    df = df.dropna(subset=['lat', 'lon', 'magnitude', 'depth'])
    df['map_size'] = df['magnitude'].fillna(0) * 10
    
    return df