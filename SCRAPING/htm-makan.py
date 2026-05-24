import pandas as pd
import time
import re
import random
import statistics
import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= KONFIGURASI =================
FILE_INPUT = 'tempat-makan_empty.xlsx'
# FILE_OUTPUT dibuat secara dinamis seperti htm-hotel.py:
# updated_filename = f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx"
# ===============================================

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # Menggunakan User-Agent modern macOS yang sesuai dengan laptop pengguna (Mac)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # PREMIUM ANTI-DETECTION: Hapus jejak navigator.webdriver menggunakan CDP (Chrome DevTools Protocol)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    driver.set_page_load_timeout(45) # Timeout loading halaman 45 detik
    return driver

def set_gofood_location(driver, city="Malang"):
    try:
        print(f"   -> Mengatur lokasi GoFood ke '{city}' agar menu dapat ditampilkan...")
        driver.get("https://gofood.co.id/")
        time.sleep(5)
        
        # Accept cookies if any
        try:
            cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All') or contains(text(), 'Accept') or contains(text(), 'Terima semua')]")
            cookie_btn.click()
            time.sleep(1)
        except:
            pass
            
        # Cari input lokasi
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        loc_input = None
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder")
            if placeholder and any(x in placeholder.lower() for x in ["masjid", "location", "alamat", "cari"]):
                loc_input = inp
                break
        if not loc_input and inputs:
            loc_input = inputs[0]
            
        if loc_input:
            loc_input.click()
            time.sleep(1)
            loc_input.send_keys(Keys.COMMAND + "a")
            loc_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            loc_input.send_keys(city)
            time.sleep(2.5) # Tunggu dropdown autocomplete
            
            # Cari autocomplete suggestion yang mengandung nama kota
            suggestions = driver.find_elements(By.XPATH, f"//*[contains(text(), '{city}') and not(self::input) and not(self::script)]")
            clicked = False
            for sug in suggestions:
                try:
                    sug_text = sug.text.strip()
                    if sug_text and len(sug_text) < 60:
                        sug.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                loc_input.send_keys(Keys.ENTER)
                
            time.sleep(4)
            print(f"   -> Lokasi '{city}' berhasil diatur!")
            return True
        else:
            print("   -> [!] Input lokasi GoFood tidak ditemukan!")
    except Exception as e:
        print(f"   -> [!] Gagal mengatur lokasi GoFood: {str(e)[:50]}")
    return False

def get_menu_stats_from_grabfood(driver, keyword):
    try:
        # --- 1. NAVIGASI KE GOOGLE SEARCH ---
        print(f"   -> Mencari GrabFood {keyword} di Google...")
        search_url = f"https://www.google.com/search?q=GrabFood+{urllib.parse.quote(keyword)}"
        driver.get(search_url)
        
        # Jeda Manusiawi
        time.sleep(random.uniform(4, 7))

        # --- 2. CARI LINK GRABFOOD ---
        found_link = None
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='food.grab.com']")
        for link in links:
            url = link.get_attribute("href")
            # Hindari link iklan/google
            if url and "food.grab.com" in url and "google" not in url:
                found_link = url
                break
        
        if not found_link:
            return None, "Link GrabFood Tidak Ditemukan"

        print(f"   -> Mengunjungi GrabFood: {found_link[:60]}...")
        driver.get(found_link)
        
        # Tunggu loading halaman body
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(6) # GrabFood butuh waktu render
        
        # Scroll bertahap agar lazy loading menu aktif
        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Deteksi WAF atau Halaman Kosong
        if "nggak ada yang ketemu" in body_text.lower() or "nothing found" in body_text.lower() or "masuk untuk mencari lokasi" in body_text.lower():
            return None, "GrabFood Halaman Kosong (Lokasi Butuh Diatur)"
            
        if "web application firewall" in body_text.lower() or "cloudflare" in body_text.lower() or "threat to the website" in body_text.lower():
            return None, "Terblokir WAF GrabFood"
            
        lines = body_text.split('\n')
        menu_items = []
        
        # Regex Harga: Menangkap format "15.000", "Rp 15.000", "12,500"
        price_pattern = re.compile(r'^(?:Rp\.?\s?)?(\d{1,3}(?:\.\d{3})+)(?:,-)?$')

        for i, line in enumerate(lines):
            line = line.strip()
            match = price_pattern.search(line)
            if match:
                try:
                    price_str = match.group(1)
                    price = int(price_str.replace('.', '').replace(',', ''))
                    
                    if 5000 <= price <= 500000:
                        # Di GrabFood, nama menu biasanya ada 1-2 baris di ATAS harga
                        name = ""
                        for offset in range(1, 3):
                            if i - offset < 0: break
                            candidate = lines[i - offset].strip()
                            
                            # Filter kata-kata sampah
                            blacklist = ['tambah', 'add', 'sold out', 'habis', 'menu', 'promo', 'diskon', 'rekomendasi', 'terlaris', 'popular', 'populer']
                            if len(candidate) > 3 and not any(x in candidate.lower() for x in blacklist):
                                if not price_pattern.search(candidate):
                                    name = candidate
                                    break
                        
                        if name:
                            menu_items.append({'name': name, 'price': price})
                except:
                    continue

        if not menu_items:
            preview = lines[:10] if lines else "Kosong"
            return None, f"Menu GrabFood Tidak Terdeteksi. Preview: {preview}"

        # --- HITUNG STATISTIK ---
        sorted_menu = sorted(menu_items, key=lambda x: x['price'])
        prices_only = [x['price'] for x in sorted_menu]
        median_val = int(statistics.median(prices_only))
        
        result = {
            'min_name': sorted_menu[0]['name'],
            'min_price': sorted_menu[0]['price'],
            'max_name': sorted_menu[-1]['name'],
            'max_price': sorted_menu[-1]['price'],
            'median': median_val,
            'link': found_link
        }
        
        return result, "Sukses (GrabFood)"

    except Exception as e:
        return None, f"Error GrabFood: {str(e)[:50]}"

def get_menu_stats_from_gofood(driver, keyword):
    try:
        # --- 1. NAVIGASI LANGSUNG KE GOOGLE SEARCH ---
        print(f"   -> Mencari GoFood {keyword} di Google...")
        search_url = f"https://www.google.com/search?q=GoFood+{urllib.parse.quote(keyword)}"
        driver.get(search_url)
        
        # Jeda Manusiawi (random antara 5-9 detik)
        time.sleep(random.uniform(5, 9))

        # Cek apakah terdeteksi CAPTCHA
        try:
            page_source = driver.page_source.lower()
            if "unusual traffic" in page_source or "recaptcha" in page_source or "google.com/sorry" in page_source:
                print("\n[!] GOOGLE CURIGA (TERDETEKSI CAPTCHA)!")
                input("Selesaikan CAPTCHA secara manual di browser Chrome, lalu tekan ENTER di sini untuk melanjutkan...")
                time.sleep(2)
        except:
            pass

        # --- 2. CARI LINK GOFOOD ---
        found_link = None
        try:
            # Cari link GoFood di hasil pencarian
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='gofood.co.id']")
            for link in links:
                url = link.get_attribute("href")
                # Hindari link iklan/google
                if url and "gofood.co.id" in url and "google" not in url:
                    found_link = url
                    break
            
            if not found_link:
                return None, "Link GoFood Tidak Ditemukan"

            print(f"   -> Mengunjungi GoFood: {found_link[:60]}...")
            driver.get(found_link)
            
            # Tunggu loading halaman body
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # --- DETEKSI WAF / FIREWALL BLOCK ---
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "web application firewall" in body_text.lower() or "threat to the website" in body_text.lower() or "request has been interrupted" in body_text.lower():
                print("\n" + "!"*70)
                print("[!] BLOKIR WAF TERDETEKSI: GoFood mencurigai bot/aktivitas tidak biasa!")
                print("!"*70)
                print("SOLUSI MANUAL:")
                print("1. Periksa browser Chrome otomatis yang sedang terbuka.")
                print("2. Jika ada Captcha / Klik verifikasi Cloudflare, silakan selesaikan.")
                print("3. Atau biarkan browser diam selama 1-2 menit untuk mendinginkan IP.")
                print("4. Jika sudah selesai, silakan tekan ENTER di Terminal ini untuk memuat ulang...")
                input("\nTekan ENTER untuk me-reload halaman GoFood...")
                
                # Coba muat ulang halaman setelah manual action
                driver.get(found_link)
                time.sleep(5)
                WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # --- SCROLLING LEBIH AGRESIF ---
            # Scroll bertahap agar lazy loading menu aktif
            for _ in range(3): # Scroll 3 kali ke bawah
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2.5)
                # Scroll sedikit ke atas biar trigger elemen yang kelewatan
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)

        except Exception as e:
            return None, f"Error Navigasi GoFood: {str(e)[:50]}"

        # --- 3. PARSING TEKS HALAMAN ---
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Pisahkan per baris
        lines = body_text.split('\n')
        menu_items = []
        
        # Regex Harga: Menangkap format "15.000", "Rp 15.000", "12,500"
        price_pattern = re.compile(r'^(?:Rp\.?\s?)?(\d{1,3}(?:\.\d{3})+)(?:,-)?$')

        for i, line in enumerate(lines):
            line = line.strip()
            
            # Cek apakah baris ini adalah HARGA
            match = price_pattern.search(line)
            if match:
                try:
                    price_str = match.group(1)
                    price = int(price_str.replace('.', '').replace(',', ''))
                    
                    # Filter Harga Masuk Akal (5rb - 500rb)
                    if 5000 <= price <= 500000:
                        # Logika mencari nama menu mundur 1-3 baris
                        name = ""
                        for offset in range(1, 4):
                            if i - offset < 0: break
                            candidate = lines[i - offset].strip()
                            
                            # Filter kata-kata sampah UI GoFood
                            blacklist = ['tambah', 'kurang', 'sold out', 'habis', 'menu', 'promo', 'diskon', 'rekomendasi', 'terlaris']
                            if len(candidate) > 3 and not any(x in candidate.lower() for x in blacklist):
                                if not price_pattern.search(candidate):
                                    name = candidate
                                    break
                        
                        if name:
                            menu_items.append({'name': name, 'price': price})
                except:
                    continue

        if not menu_items:
            preview = lines[:10] if lines else "Kosong"
            return None, f"Menu Tidak Terdeteksi. Preview text: {preview}"

        # --- 4. HITUNG STATISTIK ---
        sorted_menu = sorted(menu_items, key=lambda x: x['price'])
        prices_only = [x['price'] for x in sorted_menu]
        median_val = int(statistics.median(prices_only))
        
        result = {
            'min_name': sorted_menu[0]['name'],
            'min_price': sorted_menu[0]['price'],
            'max_name': sorted_menu[-1]['name'],
            'max_price': sorted_menu[-1]['price'],
            'median': median_val,
            'link': found_link
        }
        
        return result, "Sukses"

    except Exception as e:
        return None, f"Error System: {str(e)[:50]}"

def main_scraper():
    # Tentukan nama file output
    updated_filename = f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx"
    
    # Cek progress lama
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

    # Muat File
    if not os.path.exists(file_to_load):
        print(f"[ERROR] File '{file_to_load}' tidak ditemukan!")
        return

    df = pd.read_excel(file_to_load)
    
    # Inisialisasi Kolom Baru (GoFood + Kolom Standar Penyelarasan)
    kolom_gofood = ['Menu_Termurah', 'Harga_Termurah', 'Menu_Termahal', 'Harga_Termahal', 'Harga_Median', 'Status']
    kolom_standar = ['Estimasi_Harga', 'Sumber_Data', 'Link_Sumber']
    
    for col in kolom_gofood + kolom_standar:
        if col not in df.columns:
            df[col] = None

    print("=== SCRAPER HARGA TEMPAT MAKAN GOFOOD & PENYELARASAN TABEL ===")
    print(f"File Input    : {file_to_load}")
    print(f"File Output   : {updated_filename}")
    print("Membuka browser Chrome...")
    
    driver = init_driver()
    set_gofood_location(driver, "Malang") # Default awal Malang
    last_set_city = "Malang"
    success_count = 0
    searches_since_restart = 0
    
    try:
        for index, row in df.iterrows():
            # Skip jika baris ini sudah sukses diproses sebelumnya (Status diawali 'Sukses')
            # Ini memastikan kita memproses ulang data yang sebelumnya gagal/kosong
            if pd.notna(row['Status']) and str(row['Status']).strip().startswith("Sukses"):
                continue
                
            keyword = str(row['Nama_Tempat'])
            city = "Surabaya" if "surabaya" in keyword.lower() else "Malang"
            
            # Restart browser berkala setiap 15 item agar bersih dari memori leaks & block
            # Ditambahkan jeda cooling down 30 detik untuk menurunkan tensi sliding-window rate limit WAF
            if searches_since_restart > 0 and searches_since_restart % 15 == 0:
                print("\n🔄 Merestart browser Chrome secara berkala & cooling down 30 detik untuk menghindari blokir...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(30) # Waktu cooling down WAF
                driver = init_driver()
                set_gofood_location(driver, city)
                last_set_city = city
                searches_since_restart = 0 # Reset counter
            
            # Jika kota berubah dari sebelumnya, setel ulang lokasi agar menu tampil benar
            if city != last_set_city:
                set_gofood_location(driver, city)
                last_set_city = city
                
            # Tambahkan counter setelah driver siap
            searches_since_restart += 1
            
            # Saring agar kota tidak double jika keyword sudah mengandung nama kota
            if "surabaya" in keyword.lower() or "malang" in keyword.lower():
                full_keyword = keyword
            else:
                full_keyword = f"{keyword} Malang" # Default ke Malang
            
            print(f"\n[{index+1}/{len(df)}] Menelusuri {full_keyword}:")
            
            data, status = get_menu_stats_from_gofood(driver, full_keyword)
            
            # Fallback ke GrabFood jika GoFood gagal
            if not data:
                print(f"    -> GoFood gagal ({status}). Mencoba fallback GrabFood...")
                data, grab_status = get_menu_stats_from_grabfood(driver, full_keyword)
                if data:
                    status = grab_status
                else:
                    status = f"GoFood: {status} | GrabFood: {grab_status}"
            
            df.at[index, 'Status'] = status
            
            if data:
                print(f"    -> BERHASIL! Median: Rp {data['median']:,}")
                print(f"       Min: {data['min_name']} (Rp {data['min_price']:,})")
                print(f"       Max: {data['max_name']} (Rp {data['max_price']:,})")
                
                # Isi Kolom GoFood Detail
                df.at[index, 'Menu_Termurah'] = data['min_name']
                df.at[index, 'Harga_Termurah'] = data['min_price']
                df.at[index, 'Menu_Termahal'] = data['max_name']
                df.at[index, 'Harga_Termahal'] = data['max_price']
                df.at[index, 'Harga_Median'] = data['median']
                
                # Isi Kolom Standar Penyelarasan (agar sama dengan hotel & wisata)
                df.at[index, 'Estimasi_Harga'] = data['median']
                df.at[index, 'Sumber_Data'] = 'GrabFood' if "GrabFood" in status else 'GoFood'
                df.at[index, 'Link_Sumber'] = data['link']
                
                success_count += 1
            else:
                print(f"    -> GAGAL: {status}")
                df.at[index, 'Estimasi_Harga'] = 0
                df.at[index, 'Sumber_Data'] = 'N/A'
                df.at[index, 'Link_Sumber'] = ''

            # Auto Save berkala setiap 5 baris
            if (index + 1) % 5 == 0:
                df.to_excel(updated_filename, index=False)
                print(f"💾 Progress sementara aman tersimpan di: {updated_filename}")
            
            # Jeda manusiawi lebih lama agar tidak dianggap aktivitas bot/scraping agresif
            time.sleep(random.uniform(7, 13))

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
        print(f"Total Data Terkumpul: {success_count}")
        print(f"Seluruh data disimpan aman di: {updated_filename}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main_scraper()