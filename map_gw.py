import json
import folium
from folium.plugins import MarkerCluster

# 1. Đọc file JSON
with open('gateway_lat_lon.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

gateways = data['gateways']

# 2. Tính tọa độ trung tâm để đặt bản đồ
lats = [g['latitude'] for g in gateways if g['latitude'] is not None]
lons = [g['longitude'] for g in gateways if g['longitude'] is not None]
center_lat = sum(lats) / len(lats) if lats else 0
center_lon = sum(lons) / len(lons) if lons else 0

# 3. Tạo bản đồ nền
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# 4. Tạo cluster
marker_cluster = MarkerCluster().add_to(m)

# 5. Thêm từng gateway vào cluster
for gw in gateways:
    lat = gw['latitude']
    lon = gw['longitude']
    if lat is None or lon is None:
        continue
    
    gw_id = gw['gatewayId']
    altitude = gw.get('altitude')
    alt_text = f"{altitude:.2f}m" if altitude is not None else "N/A"
    
    popup_text = f"""
    <b>Gateway ID:</b> {gw_id}<br>
    <b>Altitude:</b> {alt_text}<br>
    <b>Coordinates:</b> ({lat:.5f}, {lon:.5f})
    """
    
    folium.CircleMarker(
        location=[lat, lon],
        radius = 8,
        color = 'white',
        fill = True,
        fill_color = 'blue',
        fill_opacity = 0.6,
        popup = popup_text,
        tooltip=gw_id
    ).add_to(marker_cluster)

# 6. Lưu bản đồ
m.save('gateway_map.html')
print("Đã tạo file gateway_map.html. Mở bằng trình duyệt để xem kết quả.")