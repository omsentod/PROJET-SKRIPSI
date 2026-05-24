import json
import pandas as pd
import topojson as tp 
import geopandas as gpd
import folium
from shapely.geometry import Point

print("--- Memulai Validasi Dataset Wisata ---")

# ==============================================================================
# 1. PERSIAPAN PETA BATAS (Sama seperti sebelumnya)
# ==============================================================================
try:
    with open('jawa-timur-simplified-topo.json', 'r') as f:
        topo_data = json.load(f)
    print("✓ File TopoJSON terbaca")
except FileNotFoundError:
    print("X File TopoJSON tidak ditemukan!")
    exit()

# Konversi ke GeoDataFrame
topo = tp.Topology(topo_data, object_name='jawa-timur')
gdf_jatim = gpd.GeoDataFrame.from_features(json.loads(topo.to_geojson()))
gdf_jatim.set_crs(epsg=4326, inplace=True)

# Filter Malang Raya (Kota Malang, Kab. Malang, Kota Batu)
target_names = ['Malang', 'Batu']
gdf_malang_raya = gdf_jatim[gdf_jatim['kabkot'].isin(target_names)].copy()

# Klasifikasi Wilayah Administratif Malang Raya secara dinamis
def label_wilayah(row):
    if row['kabkot'] == 'Batu':
        return 'Kota Batu'
    elif row['kabkot'] == 'Malang':
        if row['geometry'].area > 0.05:
            return 'Kabupaten Malang'
        else:
            return 'Kota Malang'
    return 'Luar Malang Raya'

gdf_malang_raya['Nama_Wilayah'] = gdf_malang_raya.apply(label_wilayah, axis=1)

# Gabungkan wilayah menjadi satu kesatuan Polygon besar (untuk pengecekan cadangan/cepat)
malang_raya_polygon = gdf_malang_raya.unary_union

print("✓ Batas wilayah Malang Raya siap.")

# ==============================================================================
# 2. LOAD DATASET WISATA KAMU
# ==============================================================================
try:
    df_wisata = pd.read_excel('hotelv2.xlsx')
    print(f"✓ Dataset  terbaca: {len(df_wisata)} baris.")
except FileNotFoundError:
    print(" File  tidak ditemukan!")
    exit()

# Cleaning Koordinat (Jaga-jaga kalau ada koma pengganti titik)
def bersihkan_koordinat(val):
    if isinstance(val, str):
        return float(val.replace(',', '.'))
    return float(val)

try:
    df_wisata['Latitude'] = df_wisata['Latitude'].apply(bersihkan_koordinat)
    df_wisata['Longitude'] = df_wisata['Longitude'].apply(bersihkan_koordinat)
except Exception as e:
    print(f"X Error saat cleaning koordinat: {e}")
    exit()

# ==============================================================================
# 3. PROSES VALIDASI (POINT IN POLYGON) & VISUALISASI
# ==============================================================================
# Siapkan Peta
center_lat, center_long = -7.98, 112.63
m = folium.Map(location=[center_lat, center_long], zoom_start=10)

# Pemetaan warna estetis untuk 3 wilayah Malang Raya
color_map = {
    'Kabupaten Malang': {
        'fillColor': '#F8DE22',
        'color': '#F8DE22'
    },
    'Kota Malang': {
        'fillColor': '#D12052',
        'color': '#D12052'
    },
    'Kota Batu': {
        'fillColor': '#03AED2',
        'color': '#03AED2'
    }
}

# Gambar Garis Batas (3 Wilayah Berwarna Berbeda)
folium.GeoJson(
    gdf_malang_raya,
    name="Batas Wilayah Malang Raya",
    style_function=lambda x: {
        'fillColor': color_map.get(x['properties'].get('Nama_Wilayah', ''), {}).get('fillColor', 'gray'),
        'color': color_map.get(x['properties'].get('Nama_Wilayah', ''), {}).get('color', 'black'),
        'weight': 2,
        'fillOpacity': 0.15
    }
).add_to(m)

valid_count = 0
invalid_count = 0

print("\nSedang memplot titik ke peta...")

for index, row in df_wisata.iterrows():
    lat = row['Latitude']
    long = row['Longitude']
    nama = row['Nama_Tempat']
    
    # Buat Geometri Titik
    point = Point(long, lat) # Ingat: Point(x, y) -> (Longitude, Latitude)
    
    # CEK LOGIKA: Apakah titik ada di dalam salah satu dari 3 wilayah Malang Raya?
    status = 'INVALID (Luar Wilayah)'
    warna = 'red'
    
    for _, region_row in gdf_malang_raya.iterrows():
        if region_row['geometry'].contains(point):
            nama_wilayah = region_row['Nama_Wilayah']
            status = f"VALID ({nama_wilayah})"
            warna = 'green'
            valid_count += 1
            break
    else:
        invalid_count += 1
        # Print data yang bocor ke terminal agar ketahuan
        print(f"  ⚠ Ditemukan Data Invalid: {nama}")

    # Tambahkan Marker ke Peta
    folium.CircleMarker(
        location=[lat, long],
        radius=5,
        color=warna,
        fill=True,
        fill_color=warna,
        fill_opacity=0.7,
        popup=folium.Popup(f"<b>{nama}</b><br>Status: {status}", max_width=300)
    ).add_to(m)

# ==============================================================================
# 4. SIMPAN & LAPORAN
# ==============================================================================
# Tambahkan Legend Estetis untuk Wilayah dan Status Validasi
legend_html = '''
     <div style="position: fixed; 
     bottom: 30px; left: 30px; width: 220px; height: 210px; 
     border: 1px solid #dcdde1; z-index:9999; font-size:13px; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
     background-color:rgba(255, 255, 255, 0.95); padding: 12px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
     
     <div style="font-weight: bold; margin-bottom: 8px; color: #2f3640; border-bottom: 1px solid #f1f2f6; padding-bottom: 4px;">Penanda Wilayah</div>
     <div style="margin-bottom: 12px;">
       <div style="display: flex; align-items: center; margin-bottom: 4px;">
         <span style="display: inline-block; width: 14px; height: 14px; background-color: rgb(248, 222, 34); border: 2px solid rgb(248, 222, 34); margin-right: 8px; border-radius: 3px;"></span>
         <span style="color: #2f3640;">Kabupaten Malang</span>
       </div>
       <div style="display: flex; align-items: center; margin-bottom: 4px;">
         <span style="display: inline-block; width: 14px; height: 14px; background-color: rgb(244, 91, 38); border: 2px solid rgb(244, 91, 38); margin-right: 8px; border-radius: 3px;"></span>
         <span style="color: #2f3640;">Kota Malang</span>
       </div>
       <div style="display: flex; align-items: center; margin-bottom: 4px;">
         <span style="display: inline-block; width: 14px; height: 14px; background-color: rgb(3, 174, 210); border: 2px solid rgb(3, 174, 210); margin-right: 8px; border-radius: 3px;"></span>
         <span style="color: #2f3640;">Kota Batu</span>
       </div>
     </div>
     
     <div style="font-weight: bold; margin-bottom: 8px; color: #2f3640; border-bottom: 1px solid #f1f2f6; padding-bottom: 4px;">Status Validasi Titik</div>
     <div>
       <div style="display: flex; align-items: center; margin-bottom: 4px;">
         <span style="display: inline-block; width: 10px; height: 10px; background-color: green; border-radius: 50%; margin-right: 10px; margin-left: 2px;"></span>
         <span style="color: #2f3640;">VALID (Masuk Wilayah)</span>
       </div>
       <div style="display: flex; align-items: center;">
         <span style="display: inline-block; width: 10px; height: 10px; background-color: red; border-radius: 50%; margin-right: 10px; margin-left: 2px;"></span>
         <span style="color: #2f3640;">INVALID (Luar Wilayah)</span>
       </div>
     </div>
     
     </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))

output_file = "hotelv2.html"
m.save(output_file)

print(f"\n{'='*40}")
print("HASIL VALIDASI:")
print(f"✅ Data Valid (Hijau)   : {valid_count}")
print(f"❌ Data Invalid (Merah) : {invalid_count}")
print(f"Total Data             : {len(df_wisata)}")
print(f"{'='*40}")
print(f"Buka file '{output_file}' untuk melihat sebaran datamu.")