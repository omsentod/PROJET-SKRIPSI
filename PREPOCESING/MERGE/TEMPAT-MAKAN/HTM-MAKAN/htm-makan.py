import pandas as pd
import time
import re
import random
import statistics
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= KONFIGURASI =================
FILE_INPUT = 'tempat-makan2.xlsx'
FILE_OUTPUT = 'tempat_makan_lengkap2.xlsx'
# ===============================================

def get_menu_stats_from_gofood(driver, keyword):
    try:
        # --- 1. CARI DI GOOGLE ---
        driver.get("https://www.google.com")
        try:
            driver.find_element(By.XPATH, "//button[contains(.,'Reject')]").click()
        except:
            pass

        try:
            search_box = driver.find_element(By.NAME, "q")
            query = f"GoFood {keyword}" 
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
        except:
            return None, "Gagal Search Input"
        
        time.sleep(random.uniform(3, 5))

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
                # Cek CAPTCHA
                if "recaptcha" in driver.page_source.lower():
                    print("    [!] CAPTCHA DETECTED. Selesaikan manual lalu tekan ENTER.")
                    input() 
                    # Coba cari lagi setelah user enter
                    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='gofood.co.id']")
                    if links: found_link = links[0].get_attribute("href")

            if not found_link:
                return None, "Link GoFood Tidak Ditemukan"

            print(f"    -> Link: {found_link[:50]}...")
            driver.get(found_link)
            
            # Tunggu loading halaman
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # --- SCROLLING LEBIH AGRESIF ---
            # Scroll bertahap agar lazy loading menu aktif
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3): # Scroll 3 kali ke bawah
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # Scroll sedikit ke atas biar trigger elemen yang kelewatan
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)

        except Exception as e:
            return None, f"Error Navigasi: {str(e)[:50]}"

        # --- 3. PARSING TEKS HALAMAN (STRATEGI BARU) ---
        # Ambil seluruh teks yang terlihat oleh user
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Pisahkan per baris (GoFood biasanya memisahkan Nama dan Harga dengan baris baru)
        lines = body_text.split('\n')
        
        menu_items = []
        
        # Regex Harga: Menangkap format "15.000", "Rp 15.000", "12,500"
        # Kita cari baris yang ISINYA HANYA HARGA (dominan angka)
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
                    # Di bawah 5rb biasanya topping/sambal
                    if 5000 <= price <= 500000:
                        
                        # LOGIKA CARI NAMA:
                        # Jika baris 'i' adalah harga, maka baris 'i-1' biasanya adalah Nama Menu
                        # Kadang ada deskripsi, jadi kita cek mundur 1-3 baris
                        name = ""
                        for offset in range(1, 4):
                            if i - offset < 0: break
                            candidate = lines[i - offset].strip()
                            
                            # Filter kata-kata sampah UI GoFood
                            blacklist = ['tambah', 'kurang', 'sold out', 'habis', 'menu', 'promo', 'diskon', 'rekomendasi', 'terlaris']
                            if len(candidate) > 3 and not any(x in candidate.lower() for x in blacklist):
                                # Nama menu biasanya tidak mengandung angka ribuan (kecuali nama paket)
                                if not price_pattern.search(candidate):
                                    name = candidate
                                    break
                        
                        if name:
                            menu_items.append({'name': name, 'price': price})
                except:
                    continue

        if not menu_items:
            # Debugging: Jika gagal, simpan sedikit teks untuk dicek user
            preview = lines[:10] if lines else "Kosong"
            return None, f"Menu Tidak Terdeteksi. Preview text: {preview}"

        # --- 4. HITUNG STATISTIK ---
        sorted_menu = sorted(menu_items, key=lambda x: x['price'])
        
        # Median
        prices_only = [x['price'] for x in sorted_menu]
        median_val = int(statistics.median(prices_only))
        
        result = {
            'min_name': sorted_menu[0]['name'],
            'min_price': sorted_menu[0]['price'],
            'max_name': sorted_menu[-1]['name'],
            'max_price': sorted_menu[-1]['price'],
            'median': median_val
        }
        
        return result, "Sukses"

    except Exception as e:
        return None, f"Error System: {str(e)[:50]}"

def main_scraper():
    # Cek File
    if not os.path.exists(FILE_INPUT):
        print(f"[ERROR] File '{FILE_INPUT}' tidak ditemukan!")
        return

    df = pd.read_excel(FILE_INPUT)
    
    # Siapkan Kolom Baru
    new_cols = ['Menu_Termurah', 'Harga_Termurah', 'Menu_Termahal', 'Harga_Termahal', 'Harga_Median', 'Status']
    for col in new_cols:
        if col not in df.columns:
            df[col] = None

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # User Agent biar ga dikira bot
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print("\n=== SCRAPING MENU LENGKAP (GOFOOD) ===")
    
    try:
        for index, row in df.iterrows():
            # Skip jika sudah ada data median
            if pd.notna(row['Harga_Median']) and row['Harga_Median'] > 0:
                continue
                
            keyword = str(row['Nama_Tempat'])
            city = "Surabaya" if "Surabaya" in keyword else "Malang"
            full_keyword = f"{keyword} {city}"
            
            print(f"[{index+1}/{len(df)}] {full_keyword} ...")
            
            data, status = get_menu_stats_from_gofood(driver, full_keyword)
            
            df.at[index, 'Status'] = status
            
            if data:
                print(f"    -> OK: Median Rp {data['median']:,}")
                print(f"       Min: {data['min_name']} ({data['min_price']:,})")
                print(f"       Max: {data['max_name']} ({data['max_price']:,})")
                
                df.at[index, 'Menu_Termurah'] = data['min_name']
                df.at[index, 'Harga_Termurah'] = data['min_price']
                df.at[index, 'Menu_Termahal'] = data['max_name']
                df.at[index, 'Harga_Termahal'] = data['max_price']
                df.at[index, 'Harga_Median'] = data['median']
            else:
                print(f"    -> GAGAL: {status}")

            # Auto Save
            if index % 5 == 0:
                df.to_excel(FILE_OUTPUT, index=False)
            
            time.sleep(random.uniform(4, 7))

    except KeyboardInterrupt:
        print("\n[STOP] Dihentikan User.")
    finally:
        df.to_excel(FILE_OUTPUT, index=False)
        driver.quit()
        print(f"\nSelesai. Cek file: {FILE_OUTPUT}")

if __name__ == "__main__":
    main_scraper()