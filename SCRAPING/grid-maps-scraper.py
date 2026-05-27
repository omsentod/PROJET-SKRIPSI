import time
import re
import json
import random
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Spasial Geospatial imports
import topojson as tp
from shapely.geometry import shape, Point
from shapely.ops import unary_union

# ==============================================================================
# 1. PENGATURAN GEOSPATIAL & GRID GENERATOR
# ==============================================================================
def generate_grid_malang_raya(topojson_path='jawa-timur-simplified-topo.json', step=0.05):

    if not os.path.exists(topojson_path):
        print(f"[ERROR] File '{topojson_path}' tidak ditemukan!")
        return []

    print(f"Mengurai batas wilayah Malang Raya dari '{topojson_path}'...")
    with open(topojson_path, 'r') as f:
        topo_data = json.load(f)
    
    # Konversi TopoJSON ke GeoJSON
    topo = tp.Topology(topo_data, object_name='jawa-timur')
    geojson = json.loads(topo.to_geojson())
    features = geojson['features']
    
    # Ambil batas administrasi Malang Raya (Kabupaten Malang, Kota Malang, Kota Batu)
    # Index 6: Kabupaten Malang, Index 31: Kota Malang, Index 37: Kota Batu
    polys = []
    for idx in [6, 31, 37]:
        try:
            poly_shape = shape(features[idx]['geometry'])
            polys.append(poly_shape)
        except Exception as e:
            print(f"Gagal mengambil polygon indeks {idx}: {e}")
            
    if not polys:
        print("[ERROR] Batas wilayah tidak dapat dibuat.")
        return []
        
    # Satukan ketiga batas administratif tersebut menjadi satu region Malang Raya
    malang_raya_area = unary_union(polys)
    bounds = malang_raya_area.bounds  # (min_lng, min_lat, max_lng, max_lat)
    
    min_lng, min_lat, max_lng, max_lat = bounds
    grid_points = []
    
    # Iterasi di dalam bounding box
    lng = min_lng
    while lng <= max_lng:
        lat = min_lat
        while lat <= max_lat:
            pt = Point(lng, lat)
            # Filter Point-in-Polygon (PIP) agar titik di dalam batas wilayah saja
            if malang_raya_area.contains(pt):
                grid_points.append((lat, lng))
            lat += step
        lng += step
        
    print(f"✓ Berhasil menghasilkan {len(grid_points)} titik grid pencarian.")
    return grid_points, malang_raya_area

# ==============================================================================
# 2. FUNGSI EKSTRAKSI DATA & UTILITAS SELENIUM
# ==============================================================================
def get_lat_long_from_url(url):
    if not url: return None, None
    try:
        coords = re.search(r'!3d([-0-9.]+)!4d([-0-9.]+)', url)
        if coords:
            return float(coords.group(1)), float(coords.group(2))
    except:
        return None, None
    return None, None

def clean_rating_advanced(element):
    rating = "0"
    ulasan = 0
    try:
        star_element = element.find_element(By.CSS_SELECTOR, "span[aria-label*='bintang'], span[aria-label*='stars']")
        label = star_element.get_attribute("aria-label")
        match = re.search(r'(\d+[.,]\d+)', label)
        if match:
            rating = match.group(1).replace(',', '.')
        
        if "ulasan" in label or "reviews" in label:
             reviews_match = re.findall(r'([\d.]+)\s(?:ulasan|reviews)', label)
             if reviews_match:
                 ulasan = int(reviews_match[0].replace('.',''))
        else:
             text = element.text
             match_bracket = re.search(r'\(([\d.,]+K?)\)', text)
             if match_bracket:
                 raw = match_bracket.group(1).replace('.','').replace(',','')
                 if 'K' in raw: ulasan = int(float(raw.replace('K','')) * 1000)
                 else: ulasan = int(raw)
    except:
        pass
    return rating, ulasan

def extract_category_safe(full_text_list):
    whitelist = ["Hotel", "Penginapan", "Villa", "Taman", "Restoran", "Warung", "Kafe", 
                 "Pantai", "Gunung", "Museum", "Masjid", "Mall", "Kolam Renang", "Wisata"]
    try:
        for line in full_text_list:
            clean = line.strip()
            for w in whitelist:
                if w.lower() in clean.lower() and len(clean.split()) < 6:
                    return clean
    except:
        pass
    return "Wisata Umum"

def scroll_google_maps_feed(driver, max_scrolls=20):
    """
    Scroll feed Google Maps lokal untuk meload seluruh tempat wisata terdekat.
    Karena areanya kecil, max_scrolls dibatasi agar proses lebih cepat.
    """
    try:
        wait = WebDriverWait(driver, 8)
        scrollable_div = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
        )
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        stagnant_count = 0
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable_div)
            time.sleep(1.8)
            
            # Deteksi pesan akhir halaman
            end_messages = ["reached the end", "mencapai akhir daftar", "sampai di akhir"]
            page_text = scrollable_div.text.lower()
            if any(msg in page_text for msg in end_messages):
                break
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                stagnant_count += 1
                if stagnant_count >= 3:
                    break
                driver.execute_script("arguments[0].scrollBy(0, -100);", scrollable_div)
                time.sleep(0.3)
                driver.execute_script("arguments[0].scrollBy(0, 100);", scrollable_div)
            else:
                stagnant_count = 0
                last_height = new_height
            
            scroll_count += 1
    except:
        pass

# ==============================================================================
# 3. ENGINE UTAMA SCRAPER BERBASIS GRID (GRID SCRAPER ENGINE)
# ==============================================================================
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(40) # Timeout loading halaman 40 detik
    return driver

def run_grid_scraper(keyword, step_size=0.05, max_points_test=None, zoom=14, min_rating=0.0, min_reviews=0):
    """
    Melakukan scraping Google Maps menyusuri koordinat grid Malang Raya dengan ketahanan tinggi.
    """
    # 1. Dapatkan Titik Grid Spasial
    grid_data = generate_grid_malang_raya('jawa-timur-simplified-topo.json', step=step_size)
    if not grid_data:
        return
    points, boundary_area = grid_data
    
    # Mode Uji Coba (Skala Kecil)
    if max_points_test is not None:
        points = points[:max_points_test]
        print(f"⚠️ Menjalankan MODE UJI COBA terbatas pada {len(points)} titik grid pertama.")
    
    total_points = len(points)
    
    collected_places = {} 
    output_filename = f"{keyword.replace(' ', '_')}_Grid_Progress.xlsx"
    final_filename = f"{keyword.replace(' ', '_')}_Grid_Final.xlsx"
    state_filename = f"{keyword.replace(' ', '_')}_Grid_State.json"
    
    start_index = 0
    
    # 2. Cek apakah ada data sesi sebelumnya untuk Resume (Lanjut)
    if os.path.exists(state_filename) and (os.path.exists(output_filename) or os.path.exists(final_filename)):
        print("\n🔄 DATA KEMAJUAN SEBELUMNYA DITEMUKAN!")
        pilihan_resume = input("Apakah Anda ingin MELANJUTKAN scraping yang sempat terhenti? (y/n): ").strip().lower()
        
        if pilihan_resume == 'y':
            try:
                # Load data yang sudah ter-save
                src_file = output_filename if os.path.exists(output_filename) else final_filename
                df_ex = pd.read_excel(src_file)
                
                # Masukkan data lama ke memori collected_places
                for _, row in df_ex.iterrows():
                    nama = row['Nama_Tempat']
                    collected_places[nama] = {
                        'Nama_Tempat': nama,
                        'Latitude': row['Latitude'],
                        'Longitude': row['Longitude'],
                        'Rating': row['Rating'],
                        'Jumlah_Ulasan': row['Jumlah_Ulasan'],
                        'Kategori': row['Kategori'],
                        'Link': row.get('Link', '')
                    }
                
                # Baca indeks terakhir yang sukses diproses
                with open(state_filename, 'r') as sf:
                    state_data = json.load(sf)
                    start_index = state_data.get('last_index', 0) + 1
                    
                print(f"✓ Berhasil memuat {len(collected_places)} data unik.")
                print(f"✓ Melanjutkan dari titik grid ke-{start_index + 1}...")
            except Exception as e:
                print(f"⚠️ Gagal memuat data lama: {e}. Memulai dari awal...")
                start_index = 0
                collected_places = {}
    
    if start_index >= total_points:
        print("✓ Seluruh titik koordinat sudah selesai diproses sebelumnya!")
        return

    # 3. Inisialisasi Driver Chrome
    print("\nMenyiapkan browser Chrome...")
    driver = init_driver()
    
    print("\n" + "="*60)
    print(f"MEMULAI SCRAPING GRID: '{keyword}'")
    print(f"Jumlah Titik Grid: {total_points - start_index} dari total {total_points}")
    print(f"Filter Aktif: Rating >= {min_rating}, Ulasan >= {min_reviews}")
    print(f"Perkiraan Sisa Waktu: {(total_points - start_index) * 20 // 60} menit")
    print("="*60 + "\n")
    
    try:
        for idx in range(start_index, total_points):
            lat, lng = points[idx]
            
            # Restart browser setiap 25 titik grid agar Chrome tetap ringan & bebas bocor memori
            if idx > start_index and idx % 25 == 0:
                print("\n🔄 Merestart browser Chrome secara berkala untuk menjaga stabilitas...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(2)
                driver = init_driver()
            
            print(f"[{idx+1}/{total_points}] Menelusuri koordinat ({lat:.5f}, {lng:.5f}) ... ", end="", flush=True)
            
            # Navigasi Google Maps dengan penanganan timeout & crash
            maps_url = f"https://www.google.com/maps/search/{keyword}/@{lat},{lng},{zoom}z"
            try:
                driver.get(maps_url)
            except TimeoutException:
                print("⚠️ Halaman lambat dimuat (Timeout 40s), melewati titik ini.")
                continue
            except Exception as e:
                print(f"⚠️ Gagal mengakses halaman ({e}), melewati titik ini.")
                continue
            
            # Jeda rendering halaman
            time.sleep(random.uniform(4, 6))
            
            # Cek Captcha
            try:
                page_src = driver.page_source.lower()
                if "unusual traffic" in page_src or "recaptcha" in page_src or "google.com/sorry" in page_src:
                    print("\n[!] TERDETEKSI CAPTCHA!")
                    input("Selesaikan CAPTCHA di browser Chrome secara manual, kemudian kembali ke sini dan tekan ENTER untuk melanjutkan...")
                    time.sleep(2)
            except:
                pass
            
            # Scroll feed lokal di koordinat ini
            scroll_google_maps_feed(driver, max_scrolls=15)
            
            # Ekstraksi Elemen Kartu Wisata
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            except:
                print("0 data (feed error)")
                continue
                
            extracted_in_grid = 0
            
            for card in cards:
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    url = link_el.get_attribute('href')
                    nama = link_el.get_attribute('aria-label')
                    
                    if not nama or nama in collected_places:
                        continue
                    
                    # Dapatkan koordinat tempat wisata tersebut
                    place_lat, place_lng = get_lat_long_from_url(url)
                    if not place_lat or not place_lng:
                        continue
                    
                    # Validasi Spasial Tambahan (PIP): Pastikan tempat wisata 100% berada di Malang Raya
                    place_pt = Point(place_lng, place_lat)
                    if not boundary_area.contains(place_pt):
                        continue
                        
                    # Ekstraksi Info Pendukung
                    rating, ulasan = clean_rating_advanced(card)
                    
                    try:
                        rating_val = float(rating)
                    except:
                        rating_val = 0.0
                    
                    # Filter kualitas tempat (anti-bodong)
                    if rating_val < min_rating or ulasan < min_reviews:
                        print(f"\n   [FILTER] Melewati '{nama}' (Rating: {rating_val}, Ulasan: {ulasan} tidak memenuhi kriteria minimum)")
                        continue
                        
                    try:
                        full_text = card.text.split('\n')
                        kategori = extract_category_safe(full_text)
                    except StaleElementReferenceException:
                        continue
                    except:
                        kategori = "Wisata Umum"
                    
                    # Simpan ke memori
                    collected_places[nama] = {
                        'Nama_Tempat': nama,
                        'Latitude': place_lat,
                        'Longitude': place_lng,
                        'Rating': rating,
                        'Jumlah_Ulasan': ulasan,
                        'Kategori': kategori,
                        'Link': url
                    }
                    extracted_in_grid += 1
                    print(f"\n   [✓] Berhasil disimpan: '{nama}' (Rating: {rating_val}, Ulasan: {ulasan}, Kategori: {kategori})")
                except:
                    continue
            
            print(f"Ditemukan {extracted_in_grid} data baru (Total Terkumpul: {len(collected_places)})")
            
            # Simpan kemajuan & simpan state index setiap titik koordinat sukses diproses
            try:
                with open(state_filename, 'w') as sf:
                    json.dump({'last_index': idx}, sf)
            except:
                pass
                
            # Auto-save ke Excel setiap 5 titik grid selesai
            if (idx + 1) % 5 == 0 and collected_places:
                try:
                    df_temp = pd.DataFrame(list(collected_places.values()))
                    df_temp['Id_Tempat'] = range(1, len(df_temp) + 1)
                    cols = ['Id_Tempat', 'Nama_Tempat', 'Rating', 'Jumlah_Ulasan', 'Kategori', 'Latitude', 'Longitude', 'Link']
                    df_temp = df_temp[cols]
                    df_temp.to_excel(output_filename, index=False)
                    
                    # Tampilkan daftar data yang terkumpul secara berkala dan berurutan
                    print("\n" + "="*80)
                    print(f"📊 LAPORAN KEMAJUAN BERKALA: DATA TERKUMPUL (Total: {len(df_temp)} tempat)")
                    print("="*80)
                    print(f"{'No.':<4} | {'Nama Tempat':<35} | {'Rating':<6} | {'Ulasan':<6} | {'Kategori'}")
                    print("-"*80)
                    for index, row in df_temp.iterrows():
                        print(f"{row['Id_Tempat']:<4} | {row['Nama_Tempat'][:35]:<35} | {row['Rating']:<6} | {row['Jumlah_Ulasan']:<6} | {row['Kategori']}")
                    print("="*80 + "\n")
                except Exception as e:
                    print(f"\n⚠️ Gagal auto-save / menampilkan data: {e}")
                
            # Jeda manusiawi antar koordinat grid
            time.sleep(random.uniform(2, 4))
            
    except KeyboardInterrupt:
        print("\n\n🛑 Proses scraping dihentikan secara paksa oleh Pengguna!")
    finally:
        try:
            driver.quit()
        except:
            pass
        
        # Ekspor data final setelah selesai/dihentikan
        if collected_places:
            df_final = pd.DataFrame(list(collected_places.values()))
            df_final['Id_Tempat'] = range(1, len(df_final) + 1)
            cols = ['Id_Tempat', 'Nama_Tempat', 'Rating', 'Jumlah_Ulasan', 'Kategori', 'Latitude', 'Longitude', 'Link']
            df_final = df_final[cols]
            df_final.to_excel(final_filename, index=False)
            
            # Tampilkan daftar data final yang terkumpul secara berurutan
            print("\n" + "="*80)
            print(f"🏆 HASIL AKHIR DATA TERKUMPUL SECARA BERURUTAN (Total: {len(df_final)} tempat)")
            print("="*80)
            print(f"{'No.':<4} | {'Nama Tempat':<35} | {'Rating':<6} | {'Ulasan':<6} | {'Kategori'}")
            print("-"*80)
            for index, row in df_final.iterrows():
                print(f"{row['Id_Tempat']:<4} | {row['Nama_Tempat'][:35]:<35} | {row['Rating']:<6} | {row['Jumlah_Ulasan']:<6} | {row['Kategori']}")
            print("="*80 + "\n")
            
            # Jika benar-benar selesai memproses seluruh titik koordinat, hapus state progress
            if 'idx' in locals() and idx == total_points - 1:
                if os.path.exists(output_filename): os.remove(output_filename)
                if os.path.exists(state_filename): os.remove(state_filename)
                print("\n" + "="*60)
                print("✓ SELURUH PROSES SCRAPING SELESAI PENUH!")
                print(f"Total Data Unik Berhasil Didapatkan: {len(df_final)}")
                print(f"Data tersimpan di file: {final_filename}")
                print("="*60 + "\n")
            else:
                # Jika terhenti di tengah jalan, ingatkan user bahwa data sudah aman tersimpan sementara
                print("\n" + "="*60)
                print("⚠️ PROSES TERHENTI / BELUM SELESAI PENUH")
                print(f"Kemajuan Anda berhasil disimpan sementara di: {final_filename}")
                print(f"Total Data Terkumpul Sejauh Ini: {len(df_final)}")
                print(f"Anda dapat melanjutkan nanti dengan memilih 'y' saat menjalankan script.")
                print("="*60 + "\n")
        else:
            print("\n✗ Proses selesai tetapi tidak ada data baru yang berhasil dikumpulkan.")

# ==============================================================================
# 4. RUNNER MENU
# ==============================================================================
if __name__ == "__main__":
    print("="*60)
    print("     SELENIUM GEOSPATIAL GRID SCRAPER (MALANG RAYA)")
    print("="*60)
    
    keyword_input = input("Masukkan Kata Kunci (misal: Wisata): ").strip()
    
    print("\n--- Pengaturan Filter Kualitas Tempat (Anti-Bodong) ---")
    min_rating_input = input("Masukkan Rating Minimum (contoh: 3.5, tekan Enter untuk mengabaikan): ").strip()
    min_reviews_input = input("Masukkan Jumlah Ulasan Minimum (contoh: 5, tekan Enter untuk mengabaikan): ").strip()
    
    try:
        min_rating = float(min_rating_input) if min_rating_input else 0.0
    except ValueError:
        print("⚠️ Input rating tidak valid, default diatur ke 0.0")
        min_rating = 0.0

    try:
        min_reviews = int(min_reviews_input) if min_reviews_input else 0
    except ValueError:
        print("⚠️ Input ulasan tidak valid, default diatur ke 0")
        min_reviews = 0
    
    print("\n--- Pilihan Tingkat Kerapatan Pencarian (Grid Step) ---")
    print("1. Cepat & Efisien (Kerapatan ~5.6 km, ~124 Titik Grid)")
    print("2. Detail & Menyeluruh (Kerapatan ~3.3 km, ~343 Titik Grid)")
    print("3. Uji Coba Cepat (Menjalankan hanya 3 Titik Pertama untuk Test)")
    pilihan = input("Pilih Opsi (1/2/3): ").strip()
    
    # Parsing pilihan input
    if pilihan == "3":
        run_grid_scraper(keyword_input, step_size=0.05, max_points_test=3, min_rating=min_rating, min_reviews=min_reviews)
    elif pilihan == "2":
        run_grid_scraper(keyword_input, step_size=0.03, min_rating=min_rating, min_reviews=min_reviews)
    else:
        run_grid_scraper(keyword_input, step_size=0.05, min_rating=min_rating, min_reviews=min_reviews)
