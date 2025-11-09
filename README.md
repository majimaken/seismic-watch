# Seismic Watch: Streamlit Dashboard

## Overview
This repository hosts the Streamlit application for **Seismic Watch** and is designed for visualizing live earthquake data. 

### Release Pipeline:
- Interactive map with filtering and tooltips
- New page with focus on region (user can select the top 10 active regions)
- Information page
- Information page with:
Tsunami Events Map: If a tsunami event is present (tsunami: 1), filter the data and display a dedicated map for those high-risk events. Richter Scale Context: Use an expander to provide a clear, detailed table explaining the typical effects associated with different magnitude ranges (e.g., Mag 5.0-5.9 = Moderate, felt widely, minor damage). Depth Hazard Explanation: Use an image tag like `` to visually explain the difference between shallow (crustal) and deep (slab) earthquakes.

## Installation

### 1. Getting Started
```bash
git clone [https://github.com/majimaken/seismic-watch.git](https://github.com/majimaken/seismic-watch.git)
cd seismic-watch

# Activate your existing virtual environment (as seen in your command prompt)
.\venv\Scripts\activate

# Install necessary libraries
pip install requirements.txt

# Run app
streamlit run app.py
```

The application will automatically open in your web browser, typically at http://localhost:8501.
