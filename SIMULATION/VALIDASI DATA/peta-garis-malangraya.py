import json
import os
import topojson as tp
import geopandas as gpd
import folium

def main():
    print("="*60)
    print("MEMBUAT PETA GARIS BATAS MALANG RAYA")
    print("="*60)
    
    print("1. Membaca data TopoJSON 'jawa-timur-simplified-topo.json'...")
    try:
        with open('jawa-timur-simplified-topo.json', 'r') as f:
            topo_data = json.load(f)
    except FileNotFoundError:
        print("File 'jawa-timur-simplified-topo.json' tidak ditemukan!")
        return

    # Konversi TopoJSON ke GeoJSON dan masukkan ke GeoDataFrame
    topo = tp.Topology(topo_data, object_name='jawa-timur')
    gdf_jatim = gpd.GeoDataFrame.from_features(json.loads(topo.to_geojson()))
    gdf_jatim.set_crs(epsg=4326, inplace=True)

    # Filter khusus wilayah Malang Raya
    target_names = ['Malang', 'Batu']
    gdf_malang_raya = gdf_jatim[gdf_jatim['kabkot'].isin(target_names)].copy()

    # Fungsi untuk memisahkan Kota Malang dan Kabupaten Malang (Berdasarkan luasan area geometry)
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

    print("2. Membuat visualisasi peta HTML dengan Folium...")
    # Pusatkan peta di Malang Raya
    center_lat, center_long = -7.98, 112.63
    m = folium.Map(location=[center_lat, center_long], zoom_start=10)

    # Hanya menampilkan garis batas dengan warna yang berbeda
    color_map = {
        'Kabupaten Malang': {'color': '#F8DE22'}, # Kuning
        'Kota Malang':      {'color': '#D12052'}, # Merah
        'Kota Batu':        {'color': '#03AED2'}  # Biru
    }

    folium.GeoJson(
        gdf_malang_raya,
        name="Garis Batas Malang Raya",
        style_function=lambda x: {
            'color': color_map.get(x['properties'].get('Nama_Wilayah', ''), {}).get('color', 'black'),
            'weight': 3, # Ketebalan garis
            'fillOpacity': 0.1 # Fill sedikit transparan agar garisnya saja yang menonjol
        }
    ).add_to(m)

    # Menambahkan Legenda Custom HTML
    legend_html = '''
         <div style="position: fixed; bottom: 30px; left: 30px; width: 220px;
         border: 1px solid #dcdde1; z-index:9999; font-size:13px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
         background-color:rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
         <div style="font-weight: bold; font-size: 14px; border-bottom: 2px solid #2c3e50; padding-bottom: 5px; margin-bottom: 10px; color: #2f3640;">
             🗺️ Garis Batas Wilayah
         </div>
         
         <div style="font-size: 12px; color: #57606f; line-height: 1.8;">
             <span style="display:inline-block; width: 24px; height: 3px; background-color: #D12052; margin-right: 6px; vertical-align: middle;"></span>Kota Malang<br>
             <span style="display:inline-block; width: 24px; height: 3px; background-color: #F8DE22; margin-right: 6px; vertical-align: middle;"></span>Kab. Malang<br>
             <span style="display:inline-block; width: 24px; height: 3px; background-color: #03AED2; margin-right: 6px; vertical-align: middle;"></span>Kota Batu
         </div>
         </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Output file
    output_dir = 'HASIL-VALIDASI' # Sesuai dengan folder output project ini sebelumnya
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'peta_garis_malang_raya.html')
    m.save(output_file)

    print(f"✓ SELESAI! Peta berhasil disimpan di: {output_file}")

if __name__ == "__main__":
    main()
