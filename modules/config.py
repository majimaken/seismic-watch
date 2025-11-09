# --- CONFIGURATION / CONSTANTS ---

USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

# Columns to display in the Streamlit dataframe
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