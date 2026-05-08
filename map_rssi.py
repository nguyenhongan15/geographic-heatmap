"""
LoRaWAN Coverage Heatmap
- Đọc file response JSON từ ChirpStack
- Vẽ 3 lớp: HeatMap mật độ, HeatMap theo RSSI, các điểm RSSI rời rạc
- Đánh dấu vị trí các Gateway
"""

import json
import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd

INPUT_FILE = 'response_1778245310640.json'
OUTPUT_FILE = 'lorawan_coverage_heatmap.html'

# 1) ĐỌC & PHẲNG HOÁ DỮ LIỆU ---------------------------------------------------
with open(INPUT_FILE, 'r') as f:
    raw = json.load(f)

records = []
gateways = {}  # gatewayId -> (lat, lon)

for msg in raw:
    obj = msg.get('object') or {}
    lat_raw = obj.get('gnss_latitude')
    lon_raw = obj.get('gnss_longitude')
    if lat_raw is None or lon_raw is None:
        continue  # bỏ qua bản tin không có GPS

    lat = lat_raw / 1e7
    lon = lon_raw / 1e7

    # Lấy RSSI/SNR tốt nhất trong các gateway thu được bản tin này
    rx_list = msg.get('rxInfo') or []
    if not rx_list:
        continue
    best_rx = max(rx_list, key=lambda r: r.get('rssi', -999))

    records.append({
        'lat': lat,
        'lon': lon,
        'rssi': best_rx.get('rssi'),
        'snr': best_rx.get('snr'),
        'num_sat': obj.get('gnss_num_sat'),
        'gateway': best_rx.get('gatewayId'),
        'time': msg.get('time'),
        'num_gw_received': len(rx_list),  # bao nhiêu GW thu được bản tin này
    })

    # Cập nhật danh sách gateway
    for rx in rx_list:
        gid = rx.get('gatewayId')
        loc = rx.get('location') or {}
        if gid and gid not in gateways and 'latitude' in loc:
            gateways[gid] = (loc['latitude'], loc['longitude'])

df = pd.DataFrame(records)
print(f"Đã load {len(df)} điểm GPS hợp lệ từ {len(raw)} bản tin")
print(f"RSSI: min={df['rssi'].min()} dBm, max={df['rssi'].max()} dBm, mean={df['rssi'].mean():.1f} dBm")
print(f"Số gateway: {len(gateways)}")

# 2) TẠO BẢN ĐỒ ---------------------------------------------------------------
center = [df['lat'].mean(), df['lon'].mean()]
m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')

# --- Lớp 1: HeatMap mật độ điểm (đơn giản, mỗi điểm trọng số 1) ---
HeatMap(
    data=df[['lat', 'lon']].values.tolist(),
    name='Mật độ bản tin',
    radius=12,
    blur=18,
    min_opacity=0.3,
).add_to(m)

# --- Lớp 2: HeatMap theo RSSI (tín hiệu mạnh = "nóng") ---
# RSSI là số âm (-135 -> -55). Đổi sang trọng số 0..1: tín hiệu càng mạnh thì
# trọng số càng cao -> heatmap đỏ ở vùng phủ tốt, xanh ở vùng yếu/biên.
rssi_min, rssi_max = -120, -60  # cắt 2 đầu để màu rõ ràng
df['rssi_weight'] = ((df['rssi'].clip(rssi_min, rssi_max) - rssi_min)
                     / (rssi_max - rssi_min))

HeatMap(
    data=df[['lat', 'lon', 'rssi_weight']].values.tolist(),
    name='Cường độ RSSI (đỏ = sóng tốt)',
    radius=15,
    blur=20,
    min_opacity=0.4,
    gradient={0.0: 'blue', 0.3: 'cyan', 0.5: 'lime',
              0.75: 'yellow', 1.0: 'red'},
    show=False,  # mặc định ẩn, người dùng bật bằng layer control
).add_to(m)

# --- Lớp 3: Marker từng điểm với tooltip RSSI (cluster cho nhẹ) ---
points_layer = folium.FeatureGroup(name='Điểm đo (click để xem RSSI)', show=False)
cluster = MarkerCluster().add_to(points_layer)

def rssi_color(rssi):
    if rssi >= -85:   return 'green'
    if rssi >= -100:  return 'lightgreen'
    if rssi >= -110:  return 'orange'
    if rssi >= -120:  return 'red'
    return 'darkred'

# Lấy mẫu để bản đồ không quá nặng (3500 marker là nhiều)
sample = df.sample(min(1000, len(df)), random_state=1)
for _, row in sample.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=4,
        color=rssi_color(row['rssi']),
        fill=True,
        fill_opacity=0.8,
        popup=folium.Popup(
            f"<b>RSSI:</b> {row['rssi']} dBm<br>"
            f"<b>SNR:</b> {row['snr']} dB<br>"
            f"<b>Sat:</b> {row['num_sat']}<br>"
            f"<b>GW thu:</b> {row['num_gw_received']}<br>"
            f"<b>Time:</b> {row['time']}",
            max_width=250,
        ),
    ).add_to(cluster)
points_layer.add_to(m)

# --- Lớp 4: Vị trí các Gateway ---
gw_layer = folium.FeatureGroup(name='Gateway', show=True)
for gid, (glat, glon) in gateways.items():
    folium.Marker(
        location=[glat, glon],
        tooltip=f'Gateway: {gid}',
        icon=folium.Icon(color='black', icon='tower-cell', prefix='fa'),
    ).add_to(gw_layer)
gw_layer.add_to(m)

# Layer control + tiêu đề
folium.LayerControl(collapsed=False).add_to(m)
title_html = '''
<div style="position: fixed; top: 10px; left: 50px; z-index:9999;
            background: white; padding: 8px 14px; border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,.2); font-family: sans-serif;">
  <b>LoRaWAN Coverage Heatmap — Đà Nẵng</b><br>
  <small>{n} điểm | {g} gateway | RSSI {rmin} → {rmax} dBm</small>
</div>'''.format(n=len(df), g=len(gateways),
                rmin=int(df['rssi'].min()), rmax=int(df['rssi'].max()))
m.get_root().html.add_child(folium.Element(title_html))

m.save(OUTPUT_FILE)
print(f"\nĐã lưu bản đồ -> {OUTPUT_FILE}")