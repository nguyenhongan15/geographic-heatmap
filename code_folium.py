import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np

np.random.seed(42)
data = pd.DataFrame({
    'lat': np.random.normal(16.0544, 0.05, 500),
    'lon': np.random.normal(108.2022, 0.05, 500),
    'weight': np.random.rand(500)
})

m = folium.Map(
    location=[16.0544, 108.2022],
    zoom_start=12,
    title='OpenStreetMap'
)

heat_data = data[['lat', 'lon', 'weight']].values.tolist()

HeatMap(
    heat_data,
    radius=15,
    blur=20,
    max_zoom=13,
    min_opacity=0.4,
    gradient={
        0.2: 'blue',
        0.4: 'cyan',
        0.6: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    }
).add_to(m)

m.save('heatmap_folium.html')