import plotly.express as px
import pandas as pd
import numpy as np

# Dữ liệu mẫu
np.random.seed(42)
df = pd.DataFrame({
    'lat': np.random.normal(16.0544, 0.05, 500),
    'lon': np.random.normal(108.2022, 0.05, 500),
    'magnitude': np.random.rand(500) * 10
})

fig = px.density_map(
    df,
    lat='lat',
    lon='lon',
    z='magnitude',           # giá trị quyết định "độ nóng"
    radius=20,
    center=dict(lat=16.0544, lon=108.2022),
    zoom=11,
    map_style='open-street-map',  # không cần Mapbox token
    color_continuous_scale='Viridis',
    title='Geographic Heatmap - Đà Nẵng'
)

fig.show()
# Hoặc lưu HTML:
fig.write_html('../html_img/heatmap_plotly.html')