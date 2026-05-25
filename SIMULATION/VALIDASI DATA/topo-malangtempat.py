"""
validasi_distribusi_bulk.py - VERSI BULK
================================================================
Memproses 6 dataset sekaligus dalam satu eksekusi:
- 3 dataset lama: hotel.xlsx, tempat-makan.xlsx, wisata.xlsx
- 3 dataset V2:   hotelv2.xlsx, tempat_makanV2.xlsx, wisataV2.xlsx
Output:
- 6 file HTML peta (1 per dataset)
- Laporan distribusi konsolidasi di terminal
- File CSV & XLSX ringkasan: distribusi_summary.csv, distribusi_summary.xlsx

Cara pakai:
1. Letakkan script di folder yang sama dengan jawa-timur-simplified-topo.json
   dan keenam file Excel
2. Jalankan: python validasi_distribusi_bulk.py
3. Catat hasil di terminal (akan ada ringkasan dalam format tabel siap copy)
"""

import json
import os
import pandas as pd
import topojson as tp
import geopandas as gpd
import folium
from shapely.geometry import Point

# ==============================================================================
# KONFIGURASI BULK: 6 DATASET YANG AKAN DIPROSES
# ==============================================================================
OUTPUT_DIR = 'HASIL-VALIDASI'  
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = [
    # (label, file_path, kategori, versi)
    ('Hotel Lama',         'hotel.xlsx',                'Hotel',         'Lama'),
    ('Tempat Makan Lama',  'tempat-makan.xlsx',         'Tempat Makan',  'Lama'),
    ('Wisata Lama',        'wisata.xlsx',               'Wisata',        'Lama'),
    ('Hotel V2',           'hotelv2.xlsx',              'Hotel',         'V2'),
    ('Tempat Makan V2',    'tempat_makanV2.xlsx',       'Tempat Makan',  'V2'),
    ('Wisata V2',          'tempat_wisataV2.xlsx',      'Wisata',        'V2'),
]

# ==============================================================================
# 1. PERSIAPAN PETA BATAS (DILAKUKAN SEKALI)
# ==============================================================================
print("="*70)
print("BULK VALIDASI 6 DATASET")
print("="*70)

try:
    with open('jawa-timur-simplified-topo.json', 'r') as f:
        topo_data = json.load(f)
    print("✓ File TopoJSON terbaca")
except FileNotFoundError:
    print("X File TopoJSON tidak ditemukan!")
    exit()

topo = tp.Topology(topo_data, object_name='jawa-timur')
gdf_jatim = gpd.GeoDataFrame.from_features(json.loads(topo.to_geojson()))
gdf_jatim.set_crs(epsg=4326, inplace=True)

target_names = ['Malang', 'Batu']
gdf_malang_raya = gdf_jatim[gdf_jatim['kabkot'].isin(target_names)].copy()

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
print("✓ Batas wilayah Malang Raya siap.\n")

# ==============================================================================
# 2. UTILITY FUNCTIONS
# ==============================================================================
def bersihkan_koordinat(val):
    if isinstance(val, str):
        return float(val.replace(',', '.'))
    return float(val)


def validasi_satu_dataset(label, file_path, kategori, versi):
    """Proses satu dataset, return dict distribusi."""
    print(f"┌─────────────────────────────────────────────────────────────────┐")
    print(f"│ MEMPROSES: {label:<53} │")
    print(f"└─────────────────────────────────────────────────────────────────┘")
    
    # Cek file
    if not os.path.exists(file_path):
        print(f"  ✗ File '{file_path}' TIDAK DITEMUKAN, dilewati...\n")
        return None
    
    try:
        df = pd.read_excel(file_path)
        print(f"  ✓ Dataset terbaca: {len(df)} baris")
    except Exception as e:
        print(f"  ✗ Error membaca file: {e}\n")
        return None
    
    # Cleaning koordinat
    try:
        df['Latitude']  = df['Latitude'].apply(bersihkan_koordinat)
        df['Longitude'] = df['Longitude'].apply(bersihkan_koordinat)
    except Exception as e:
        print(f"  ✗ Error cleaning koordinat: {e}\n")
        return None
    
    # Siapkan Peta
    center_lat, center_long = -7.98, 112.63
    m = folium.Map(location=[center_lat, center_long], zoom_start=10)
    
    color_map = {
        'Kabupaten Malang': {'fillColor': '#F8DE22', 'color': '#F8DE22'},
        'Kota Malang':      {'fillColor': '#D12052', 'color': '#D12052'},
        'Kota Batu':        {'fillColor': '#03AED2', 'color': '#03AED2'}
    }
    
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
    
    # Counter per wilayah
    counter = {
        'Kota Malang': 0,
        'Kabupaten Malang': 0,
        'Kota Batu': 0,
        'Luar Malang Raya': 0
    }
    
    invalid_names = []
    places_js_data = []
    
    for _, row in df.iterrows():
        lat = row['Latitude']
        long = row['Longitude']
        nama = row['Nama_Tempat']
        
        point = Point(long, lat)
        
        status = 'INVALID (Luar Wilayah)'
        warna = 'red'
        nama_wilayah_match = None
        
        for _, region_row in gdf_malang_raya.iterrows():
            if region_row['geometry'].contains(point):
                nama_wilayah = region_row['Nama_Wilayah']
                nama_wilayah_match = nama_wilayah
                status = f"VALID ({nama_wilayah})"
                warna = 'green'
                break
        
        if nama_wilayah_match:
            counter[nama_wilayah_match] += 1
        else:
            counter['Luar Malang Raya'] += 1
            invalid_names.append(nama)
        
        # Buat popup HTML dengan tombol link ke Google Maps (Pencarian berdasarkan nama tempat agar detail tempat muncul)
        import urllib.parse
        region_context = "Batu, Jawa Timur" if "Batu" in status else "Malang, Jawa Timur"
        search_query = f"{nama}, {region_context}"
        encoded_query = urllib.parse.quote(search_query)
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        popup_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 12px; line-height: 1.5; color: #2f3640; min-width: 180px;">
                <b style="font-size: 13px; color: #2c3e50; display: block; margin-bottom: 4px;">{nama}</b>
                <span style="color: #7f8c8d;">Status:</span> <b>{status}</b><br>
                <span style="color: #7f8c8d;">Koordinat:</span> <span style="font-family: monospace; font-size: 11px;">{lat}, {long}</span>
                <div style="margin-top: 10px; border-top: 1px solid #f1f2f6; padding-top: 8px; text-align: right;">
                    <a href="{gmaps_link}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold; font-size: 11.5px; display: inline-flex; align-items: center; transition: color 0.2s;">
                        🗺️ Lihat di Google Maps &rarr;
                    </a>
                </div>
            </div>
        """
        
        folium.CircleMarker(
            location=[lat, long],
            radius=5,
            color=warna,
            fill=True,
            fill_color=warna,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320)
        ).add_to(m)
        
        # Simpan data untuk search overlay custom
        places_js_data.append({
            'name': nama,
            'lat': lat,
            'lng': long,
            'status': status
        })
        
    # Tambahkan fitur Search Overlay Custom (Fuzzy & Auto-suggest)
    places_json = json.dumps(places_js_data)
    search_html = f'''
         <div id="custom-search-box" style="position: fixed; top: 20px; right: 20px; z-index: 10000; width: 280px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
             <div style="position: relative; display: flex; align-items: center; background: white; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow: hidden; border: 1px solid #dcdde1; padding: 2px 10px;">
                 <span style="font-size: 14px; margin-right: 6px;">🔍</span>
                 <input type="text" id="search-input" placeholder="Cari nama tempat..." style="width: 100%; border: none; outline: none; padding: 6px 4px; font-size: 12.5px; color: #2f3640;">
                 <button id="clear-search" style="background: none; border: none; cursor: pointer; font-size: 13px; color: #7f8c8d; display: none; outline: none; padding: 0 4px;">✕</button>
             </div>
             <div id="suggestions-list" style="max-height: 200px; overflow-y: auto; background: white; border-radius: 8px; box-shadow: 0 6px 15px rgba(0,0,0,0.15); margin-top: 5px; display: none; border: 1px solid #f1f2f6;">
             </div>
         </div>
         
         <script>
         (function() {{
             var places = {places_json};
             var map = null;
             
             var interval = setInterval(function() {{
                 for (var key in window) {{
                     if (key.startsWith('map_') && window[key] instanceof L.Map) {{
                         map = window[key];
                         clearInterval(interval);
                         setupSearch();
                         break;
                     }}
                 }}
             }}, 100);
             
             function setupSearch() {{
                 var input = document.getElementById('search-input');
                 var clearBtn = document.getElementById('clear-search');
                 var suggestions = document.getElementById('suggestions-list');
                 
                 var markers = {{}};
                 map.eachLayer(function(layer) {{
                     if (layer instanceof L.CircleMarker || layer instanceof L.Marker) {{
                         var latLng = layer.getLatLng();
                         var key = latLng.lat.toFixed(6) + '_' + latLng.lng.toFixed(6);
                         markers[key] = layer;
                     }}
                 }});
                 
                 input.addEventListener('input', function() {{
                     var query = input.value.trim().toLowerCase();
                     if (!query) {{
                         suggestions.style.display = 'none';
                         clearBtn.style.display = 'none';
                         return;
                     }}
                     
                     clearBtn.style.display = 'block';
                     
                     var matches = places.filter(function(p) {{
                         return p.name.toLowerCase().includes(query);
                     }});
                     
                     suggestions.innerHTML = '';
                     if (matches.length === 0) {{
                         var item = document.createElement('div');
                         item.style.padding = '8px 12px';
                         item.style.fontSize = '12px';
                         item.style.color = '#7f8c8d';
                         item.innerText = 'Tempat tidak ditemukan';
                         suggestions.appendChild(item);
                     }} else {{
                         matches.slice(0, 8).forEach(function(p) {{
                             var item = document.createElement('div');
                             item.style.padding = '8px 12px';
                             item.style.cursor = 'pointer';
                             item.style.fontSize = '12px';
                             item.style.borderBottom = '1px solid #f8f9fa';
                             item.style.transition = 'background 0.2s';
                             
                             item.onmouseover = function() {{ item.style.background = '#f1f2f6'; }};
                             item.onmouseout = function() {{ item.style.background = 'white'; }};
                             
                             var idx = p.name.toLowerCase().indexOf(query);
                             var html = p.name.substring(0, idx) + 
                                        '<strong style="color: #D12052;">' + p.name.substring(idx, idx + query.length) + '</strong>' + 
                                        p.name.substring(idx + query.length);
                             
                             item.innerHTML = '<div>' + html + '</div><div style="font-size: 10px; color: #7f8c8d; margin-top: 1px;">📍 ' + p.status + '</div>';
                             
                             item.addEventListener('click', function() {{
                                 input.value = p.name;
                                 suggestions.style.display = 'none';
                                 
                                 map.setView([p.lat, p.lng], 15);
                                 
                                 var key = parseFloat(p.lat).toFixed(6) + '_' + parseFloat(p.lng).toFixed(6);
                                 var mObj = markers[key];
                                 if (mObj) {{
                                     mObj.openPopup();
                                 }} else {{
                                     var minDst = Infinity;
                                     var bestMarker = null;
                                     for (var k in markers) {{
                                         var parts = k.split('_');
                                         var mLat = parseFloat(parts[0]);
                                         var mLng = parseFloat(parts[1]);
                                         var dst = Math.pow(mLat - p.lat, 2) + Math.pow(mLng - p.lng, 2);
                                         if (dst < minDst) {{
                                             minDst = dst;
                                             bestMarker = markers[k];
                                         }}
                                     }}
                                     if (bestMarker && minDst < 0.0001) {{
                                         bestMarker.openPopup();
                                     }}
                                 }}
                             }});
                             suggestions.appendChild(item);
                         }});
                     }}
                     suggestions.style.display = 'block';
                 }});
                 
                 clearBtn.addEventListener('click', function() {{
                     input.value = '';
                     suggestions.style.display = 'none';
                     clearBtn.style.display = 'none';
                     input.focus();
                 }});
                 
                 document.addEventListener('click', function(e) {{
                     if (!document.getElementById('custom-search-box').contains(e.target)) {{
                         suggestions.style.display = 'none';
                     }}
                 }});
             }}
         }})();
         </script>
    '''
    m.get_root().html.add_child(folium.Element(search_html))
    
    # Hitung persentase untuk legenda
    total = len(df)
    km_count = counter['Kota Malang']
    kab_count = counter['Kabupaten Malang']
    kb_count = counter['Kota Batu']
    luar_count = counter['Luar Malang Raya']
    
    km_pct = (km_count / total * 100) if total > 0 else 0
    kab_pct = (kab_count / total * 100) if total > 0 else 0
    kb_pct = (kb_count / total * 100) if total > 0 else 0
    luar_pct = (luar_count / total * 100) if total > 0 else 0

    # Legend HTML Estetis
    legend_html = f'''
         <div style="position: fixed; bottom: 30px; left: 30px; width: 260px;
         border: 1px solid #dcdde1; z-index:9999; font-size:12px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
         background-color:rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
         <div style="font-weight: bold; font-size: 14px; border-bottom: 2px solid #D12052; padding-bottom: 5px; margin-bottom: 10px; color: #2f3640;">
             📊 {label}
         </div>
         
         <div style="font-weight: bold; margin-bottom: 6px; color: #2f3640; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
             Distribusi Wilayah
         </div>
         <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 12px;">
             <tr style="border-bottom: 1px solid #f1f2f6;">
                 <td style="padding: 3px 0;">🔴 Kota Malang</td>
                 <td style="text-align: right; font-weight: bold; padding: 3px 0;">{km_count} <span style="font-weight: normal; color: #7f8c8d; font-size: 11px;">({km_pct:.1f}%)</span></td>
             </tr>
             <tr style="border-bottom: 1px solid #f1f2f6;">
                 <td style="padding: 3px 0;">🟡 Kab. Malang</td>
                 <td style="text-align: right; font-weight: bold; padding: 3px 0;">{kab_count} <span style="font-weight: normal; color: #7f8c8d; font-size: 11px;">({kab_pct:.1f}%)</span></td>
             </tr>
             <tr style="border-bottom: 1px solid #f1f2f6;">
                 <td style="padding: 3px 0;">🔵 Kota Batu</td>
                 <td style="text-align: right; font-weight: bold; padding: 3px 0;">{kb_count} <span style="font-weight: normal; color: #7f8c8d; font-size: 11px;">({kb_pct:.1f}%)</span></td>
             </tr>
             <tr style="border-bottom: 1.5px solid #dcdde1; font-weight: bold; color: { '#e74c3c' if luar_count > 0 else '#2c3e50' };">
                 <td style="padding: 4px 0;">⚫ Luar Wilayah</td>
                 <td style="text-align: right; padding: 4px 0;">{luar_count} <span style="font-weight: normal; color: #7f8c8d; font-size: 11px;">({luar_pct:.1f}%)</span></td>
             </tr>
             <tr style="font-weight: bold; background-color: #f8f9fa;">
                 <td style="padding: 5px 4px;">Total Data</td>
                 <td style="text-align: right; padding: 5px 4px; color: #2980b9;">{total}</td>
             </tr>
         </table>
         
         <div style="font-weight: bold; margin-bottom: 4px; color: #2f3640; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
             Penanda Peta
         </div>
         <div style="font-size: 11px; color: #57606f; line-height: 1.5; margin-bottom: 8px;">
             <span style="display:inline-block; width: 8px; height: 8px; background-color: #D12052; border-radius: 50%; margin-right: 6px;"></span>Kota Malang (Merah)<br>
             <span style="display:inline-block; width: 8px; height: 8px; background-color: #F8DE22; border-radius: 50%; margin-right: 6px;"></span>Kab. Malang (Kuning)<br>
             <span style="display:inline-block; width: 8px; height: 8px; background-color: #03AED2; border-radius: 50%; margin-right: 6px;"></span>Kota Batu (Biru)
         </div>
         
         <div style="font-weight: bold; margin-bottom: 4px; color: #2f3640; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
             Status Validasi Pin
         </div>
         <div style="font-size: 11px; color: #57606f; line-height: 1.5;">
             <span style="display:inline-block;"></span>🟢 VALID (Dalam Wilayah)<br>
             <span style="display:inline-block;"></span>🔴 INVALID (Luar Wilayah)
         </div>
         </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Simpan peta
    base_name = os.path.basename(file_path).replace('.xlsx', '.html')
    output_file = os.path.join(OUTPUT_DIR, base_name)
    m.save(output_file)
    
    # Print hasil per dataset
    print(f"  ✓ Validasi selesai. Peta tersimpan di: {output_file}")
    print(f"  Distribusi:")
    for wilayah in ['Kota Malang', 'Kabupaten Malang', 'Kota Batu', 'Luar Malang Raya']:
        jumlah = counter[wilayah]
        persen = (jumlah / total * 100) if total > 0 else 0
        print(f"    {wilayah:<22}: {jumlah:>5} ({persen:>5.1f}%)")
    
    if invalid_names and len(invalid_names) <= 5:
        print(f"  Data Invalid: {', '.join(invalid_names[:5])}")
    elif invalid_names:
        print(f"  Data Invalid: {len(invalid_names)} data (5 pertama: {', '.join(invalid_names[:5])})")
    print()
    
    return {
        'Label': label,
        'Kategori': kategori,
        'Versi': versi,
        'File': file_path,
        'Total': total,
        'Kota Malang': counter['Kota Malang'],
        'Kabupaten Malang': counter['Kabupaten Malang'],
        'Kota Batu': counter['Kota Batu'],
        'Luar Malang Raya': counter['Luar Malang Raya']
    }


# ==============================================================================
# 3. EKSEKUSI BULK 6 DATASET
# ==============================================================================
results = []
for label, file_path, kategori, versi in DATASETS:
    result = validasi_satu_dataset(label, file_path, kategori, versi)
    if result:
        results.append(result)

# ==============================================================================
# 4. LAPORAN KONSOLIDASI
# ==============================================================================
print("\n" + "="*100)
print("RINGKASAN KONSOLIDASI HASIL VALIDASI 6 DATASET")
print("="*100)

if not results:
    print("⚠ Tidak ada dataset yang berhasil diproses.")
    exit()

df_summary = pd.DataFrame(results)

# Print ringkasan dalam format tabel
print(f"\n{'Dataset':<22} {'Total':>7} {'K.Malang':>12} {'Kab.Malang':>14} {'Kota Batu':>12} {'Luar':>10}")
print("-"*100)
for _, row in df_summary.iterrows():
    total = row['Total']
    km = row['Kota Malang']
    kab = row['Kabupaten Malang']
    kb = row['Kota Batu']
    luar = row['Luar Malang Raya']
    
    km_pct = f"({km/total*100:.1f}%)"
    kab_pct = f"({kab/total*100:.1f}%)"
    kb_pct = f"({kb/total*100:.1f}%)"
    luar_pct = f"({luar/total*100:.1f}%)"
    
    print(f"{row['Label']:<22} {total:>7} {km:>5} {km_pct:>6} {kab:>6} {kab_pct:>7} {kb:>5} {kb_pct:>6} {luar:>3} {luar_pct:>6}")

# Simpan ke CSV dan Excel
path_csv = os.path.join(OUTPUT_DIR, 'distribusi_summary.csv')
path_xlsx = os.path.join(OUTPUT_DIR, 'distribusi_summary.xlsx')
df_summary.to_csv(path_csv, index=False)
df_summary.to_excel(path_xlsx, index=False)
print(f"\n✓ Ringkasan tersimpan di: {path_csv} dan {path_xlsx}")

# ==============================================================================
# 5. FORMAT MARKDOWN SIAP COPY KE SKRIPSI
# ==============================================================================
print("\n" + "="*100)
print("FORMAT MARKDOWN SIAP COPY KE SKRIPSI (Tabel 4.2 dan Tabel 4.4):")
print("="*100)

# Tabel untuk dataset LAMA
lama = df_summary[df_summary['Versi'] == 'Lama']
if not lama.empty:
    print("\n>>> TABEL 4.2: Distribusi spasial data tahap awal (LAMA)")
    print()
    print("| Kategori | Kota Malang | Kabupaten Malang | Kota Batu | Luar Malang Raya | Total |")
    print("|---|---|---|---|---|---|")
    
    total_km = total_kab = total_kb = total_luar = total_all = 0
    for _, row in lama.iterrows():
        t = row['Total']
        km = row['Kota Malang']
        kab = row['Kabupaten Malang']
        kb = row['Kota Batu']
        luar = row['Luar Malang Raya']
        total_km += km
        total_kab += kab
        total_kb += kb
        total_luar += luar
        total_all += t
        print(f"| {row['Kategori']} | {km} ({km/t*100:.1f}%) | {kab} ({kab/t*100:.1f}%) | {kb} ({kb/t*100:.1f}%) | {luar} ({luar/t*100:.1f}%) | {t} |")
    
    if total_all > 0:
        print(f"| **Total** | **{total_km} ({total_km/total_all*100:.1f}%)** | **{total_kab} ({total_kab/total_all*100:.1f}%)** | **{total_kb} ({total_kb/total_all*100:.1f}%)** | **{total_luar} ({total_luar/total_all*100:.1f}%)** | **{total_all}** |")

# Tabel untuk dataset V2
v2 = df_summary[df_summary['Versi'] == 'V2']
if not v2.empty:
    print("\n>>> TABEL 4.4: Distribusi spasial data final (V2)")
    print()
    print("| Kategori | Kota Malang | Kabupaten Malang | Kota Batu | Luar Malang Raya | Total |")
    print("|---|---|---|---|---|---|")
    
    total_km = total_kab = total_kb = total_luar = total_all = 0
    for _, row in v2.iterrows():
        t = row['Total']
        km = row['Kota Malang']
        kab = row['Kabupaten Malang']
        kb = row['Kota Batu']
        luar = row['Luar Malang Raya']
        total_km += km
        total_kab += kab
        total_kb += kb
        total_luar += luar
        total_all += t
        print(f"| {row['Kategori']} | {km} ({km/t*100:.1f}%) | {kab} ({kab/t*100:.1f}%) | {kb} ({kb/t*100:.1f}%) | {luar} ({luar/t*100:.1f}%) | {t} |")
    
    if total_all > 0:
        print(f"| **Total** | **{total_km} ({total_km/total_all*100:.1f}%)** | **{total_kab} ({total_kab/total_all*100:.1f}%)** | **{total_kb} ({total_kb/total_all*100:.1f}%)** | **{total_luar} ({total_luar/total_all*100:.1f}%)** | **{total_all}** |")

print("\n" + "="*100)
print("✓ SELESAI! Silakan copy-paste tabel di atas ke draft skripsi.")
print("="*100)