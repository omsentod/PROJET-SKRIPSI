from collections import abc
import pandas as pd
import time
import re
import random
import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ================= KONFIGURASI =================
FILE_INPUT = 'hotelv2.xlsx' 
KATEGORI = 'hotel' # 'wisata' atau 'hotel'
# ===============================================

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

def get_price_from_google(driver, keyword, target_domain=None):
    try:
        # Gunakan navigasi langsung seperti maps scraper demi keamanan & efisiensi
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}"
        driver.get(search_url)
        
        # Jeda Manusiawi (random antara 5-10 detik)
        time.sleep(random.uniform(5, 10))
        
        # Cek apakah kena CAPTCHA
        try:
            page_source = driver.page_source.lower()
            if "unusual traffic" in page_source or "recaptcha" in page_source or "google.com/sorry" in page_source:
                print("\n[!] GOOGLE CURIGA (TERDETEKSI CAPTCHA)!")
                input("Selesaikan CAPTCHA secara manual di browser Chrome, lalu tekan ENTER di sini untuk melanjutkan...")
                time.sleep(2)
        except:
            pass
        
        # Temukan semua elemen h3 di dalam container utama #rso (hasil organik Google)
        headings = driver.find_elements(By.CSS_SELECTOR, "#rso h3")
        
        # Pola regex harga tiket/kamar
        pola_harga = r'(?:Rp\.?|IDR)\s?(\d{1,3}(?:[.,]\d{3})+(?:\d{3})?)'
        
        for h3_el in headings:
            try:
                # Dapatkan tautan (URL) asli dari rujukan ini (ancestor a tag)
                link_element = h3_el.find_element(By.XPATH, "./ancestor::a")
                link_url = link_element.get_attribute("href")
                
                # Ekstrak nama domain
                domain = urllib.parse.urlparse(link_url).netloc.lower()
                
                # JIKA target_domain ditentukan, pastikan domain hasil pencarian mengandung domain target
                if target_domain and target_domain not in domain:
                    continue
                
                # JIKA KATEGORI adalah wisata, kita wajib menyaring link agar tidak salah mengambil
                # harga hotel/stay/flight dekat lokasi wisata dari Traveloka atau Tiket.com
                if KATEGORI == 'wisata':
                    url_lower = link_url.lower()
                    if "traveloka.com" in domain or "tiket.com" in domain:
                        bad_keywords = ["hotel", "accommodation", "stay", "pesawat", "flight", "kereta", "train"]
                        if any(kw in url_lower for kw in bad_keywords):
                            continue # Ini link hotel/tiket transportasi dekat lokasi wisata, abaikan!
                
                # Temukan container hasil pencarian untuk mengambil snippet teks (naik 3 tingkat atau cari div.g/tF2Cxc/MjjYud)
                try:
                    container = h3_el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'g') or @class='tF2Cxc' or @class='MjjYud'][1]")
                except:
                    container = h3_el.find_element(By.XPATH, "./../../..")
                
                text = container.text
                
                # Cari pola harga
                matches = re.findall(pola_harga, text)
                if matches:
                    harga_mentah = matches[0]
                    harga_bersih = harga_mentah.replace('.', '').replace(',', '')
                    harga_int = int(harga_bersih)
                    
                    if harga_int > 1000: # Filter harga receh/tidak logis
                        clean_domain = domain[4:] if domain.startswith("www.") else domain
                        return harga_int, clean_domain, link_url
            except:
                continue
        
        # Fallback jika target_domain TIDAK ditentukan (Google General), baru kita parsing seluruh halaman
        if not target_domain:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            matches = re.findall(pola_harga, body_text)
            if matches:
                harga_mentah = matches[0]
                harga_bersih = harga_mentah.replace('.', '').replace(',', '')
                harga_int = int(harga_bersih)
                if harga_int > 1000:
                    return harga_int, "Google Snippet", search_url
                    
        return 0, "N/A", ""
        
    except Exception as e:
        print(f"Error saat mengekstrak harga: {e}")
        return 0, "N/A", ""

def main_price_scraper():
    updated_filename = f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx"
    
    # Cek apakah ada file progress lama untuk dilanjutkan
    if os.path.exists(updated_filename):
        print("\n" + "="*60)
        print("🔄 DATA PROGRESS SEBELUMNYA DITEMUKAN!")
        print("="*60)
        pilihan_resume = input(f"Apakah Anda ingin MELANJUTKAN scraping dari '{updated_filename}'? (y/n): ").strip().lower()
        if pilihan_resume == 'y':
            file_to_load = updated_filename
            print("✓ Melanjutkan progress kemajuan sebelumnya...")
        else:
            file_to_load = FILE_INPUT
            print("✓ Memulai dari awal (menggunakan file input mentah)...")
    else:
        file_to_load = FILE_INPUT

    try:
        df = pd.read_excel(file_to_load)
    except Exception as e:
        print(f"File '{file_to_load}' tidak dapat dimuat: {e}")
        return

    # Inisialisasi kolom jika belum ada
    if 'Estimasi_Harga' not in df.columns:
        df['Estimasi_Harga'] = 0
    if 'Sumber_Data' not in df.columns:
        df['Sumber_Data'] = 'N/A'
    if 'Link_Sumber' not in df.columns:
        df['Link_Sumber'] = ''

    print("=== SCRAPER HARGA GOOGLE MULTI-PLATFORM & ANTI-BLOCKING ===")
    print(f"File Input    : {FILE_INPUT}")
    print(f"Kategori      : {KATEGORI.upper()}")
    print("Membuka browser Chrome...")
    
    driver = init_driver()
    
    success_count = 0
    hotels_searched_since_restart = 0
    
    try:
        for index, row in df.iterrows():
            # Lewati jika sudah memiliki data harga valid yang terkumpul sebelumnya
            if pd.notna(row['Estimasi_Harga']) and row['Estimasi_Harga'] > 0:
                continue
                
            # Restart browser berkala setiap 15 hotel yang dicari agar memori Chrome bersih & terhindar dari block
            if hotels_searched_since_restart > 0 and hotels_searched_since_restart % 15 == 0:
                print("\n🔄 Merestart browser Chrome secara berkala untuk menjaga stabilitas...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(2)
                driver = init_driver()
                hotels_searched_since_restart = 0 # Reset counter pencarian setelah restart
            
            # Tambahkan counter setelah browser siap memproses baris ini
            hotels_searched_since_restart += 1
                
            nama = row['Nama_Tempat']
            
            # Tentukan daftar sumber platform berdasarkan kategori dengan filter domain target
            if KATEGORI == 'wisata':
                daftar_sumber = [
                    ("Traveloka", f"Harga tiket masuk {nama} Malang Traveloka", "traveloka.com"),
                    ("Tiket.com", f"Harga tiket masuk {nama} Malang Tiket.com", "tiket.com"),
                    ("Google General", f"Harga tiket masuk {nama} Malang 2024", None)
                ]
            else:
                daftar_sumber = [
                    ("Traveloka", f"Harga kamar {nama} Malang Traveloka", "traveloka.com"),
                    ("Tiket.com", f"Harga kamar {nama} Malang Tiket.com", "tiket.com"),
                    ("Agoda", f"Harga kamar {nama} Malang Agoda", "agoda.com"),
                    ("Google General", f"Harga kamar {nama} Malang", None)
                ]
            
            print(f"\n[{index+1}/{len(df)}] Menelusuri {nama}:")
            harga = 0
            sumber_terpilih = "N/A"
            link_terpilih = ""
            
            # Cari harga secara sekuensial (fallback jika nihil)
            for platform, query, target_domain in daftar_sumber:
                print(f"   -> Mencoba '{platform}'... ", end="", flush=True)
                harga_ditemukan, domain_ditemukan, link_ditemukan = get_price_from_google(driver, query, target_domain)
                
                if harga_ditemukan > 0:
                    harga = harga_ditemukan
                    sumber_terpilih = domain_ditemukan if platform == "Google General" else platform
                    link_terpilih = link_ditemukan
                    print(f"Berhasil! (Rp {harga:,} via {sumber_terpilih})")
                    break
                else:
                    print("Nihil")
                    time.sleep(random.uniform(2, 4))
            
            if harga > 0:
                df.at[index, 'Estimasi_Harga'] = harga
                df.at[index, 'Sumber_Data'] = sumber_terpilih
                df.at[index, 'Link_Sumber'] = link_terpilih
                success_count += 1
            else:
                print("   ✗ Semua sumber nihil.")
                df.at[index, 'Estimasi_Harga'] = 0
                df.at[index, 'Sumber_Data'] = 'N/A'
                df.at[index, 'Link_Sumber'] = ''
            
            # Auto-save berkala setiap 5 hotel
            if (index + 1) % 5 == 0:
                df.to_excel(updated_filename, index=False)
                print(f"💾 Progress sementara aman tersimpan di: {updated_filename}")

    except KeyboardInterrupt:
        print("\n🛑 Proses scraping dihentikan secara paksa oleh Pengguna!")
    finally:
        df.to_excel(updated_filename, index=False)
        try:
            driver.quit()
        except:
            pass
        print("\n" + "="*60)
        print("✓ SELESAI PENUH / KELUAR DARI PROSES")
        print(f"Total Data Harga Terkumpul: {success_count}")
        print(f"Seluruh data disimpan aman di: {updated_filename}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main_price_scraper()