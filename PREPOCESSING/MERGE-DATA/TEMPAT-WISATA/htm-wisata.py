import pandas as pd
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ================= KONFIGURASI =================
FILE_INPUT = 'merge-wisata_cleaned.xlsx' 
KATEGORI = 'wisata' # 'wisata' atau 'hotel'
# ===============================================

def get_price_from_google(driver, keyword):
    try:
        driver.get("https://www.google.com")
        
        # Cek apakah input search box ada (kadang captcha muncul di awal)
        try:
            search_box = driver.find_element(By.NAME, "q")
        except:
            print("\n[!] Terhalang CAPTCHA di awal.")
            input("Selesaikan CAPTCHA manual, lalu tekan ENTER di sini...")
            search_box = driver.find_element(By.NAME, "q")

        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        
        # Jeda Manusiawi (10-15 detik)
        time.sleep(random.uniform(8, 15))
        
        # Cek lagi apakah kena CAPTCHA setelah search
        page_source = driver.page_source.lower()
        if "unusual traffic" in page_source or "recaptcha" in page_source:
            print("\n[!] GOOGLE CURIGA! Selesaikan CAPTCHA manual di browser.")
            input("Tekan ENTER di sini setelah hasil harga muncul...")
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Regex Harga
        pola_harga = r'(?:Rp\.?|IDR)\s?(\d{1,3}(?:[.,]\d{3})+(?:\d{3})?)'
        matches = re.findall(pola_harga, body_text)
        
        if matches:
            harga_mentah = matches[0]
            harga_bersih = harga_mentah.replace('.', '').replace(',', '')
            harga_int = int(harga_bersih)
            if harga_int > 1000: # Filter harga receh
                return harga_int
                
        return 0 
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

def main_price_scraper():
    try:
        df = pd.read_excel(FILE_INPUT)
    except:
        print("File tidak ditemukan!")
        return

    if 'Estimasi_Harga' not in df.columns:
        df['Estimasi_Harga'] = 0

    options = webdriver.ChromeOptions()
    # Hapus mode headless biar kamu bisa lihat dan solve captcha
    # options.add_argument("--headless") 
    options.add_argument("--lang=id")
    
    # Anti-detect sederhana (matikan fitur otomasi browser)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print("=== SCRAPER HARGA GOOGLE (SEMI-MANUAL) ===")
    print("Jika browser berhenti di 'Unusual Traffic', selesaikan puzzle-nya manual,")
    print("lalu kembali ke terminal ini dan tekan ENTER.")
    
    try:
        for index, row in df.iterrows():
            if row['Estimasi_Harga'] > 0: continue
                
            nama = row['Nama_Tempat']
            if KATEGORI == 'wisata':
                query = f"Harga tiket masuk {nama} Malang 2024"
            else:
                query = f"Harga kamar {nama} Malang Traveloka" 
            
            print(f"[{index+1}/{len(df)}] {nama} ... ", end="")
            
            harga = get_price_from_google(driver, query)
            
            if harga > 0:
                print(f"Rp {harga}")
                df.at[index, 'Estimasi_Harga'] = harga
            else:
                print("Nihil")
            
            # Simpan tiap 5 data biar aman
            if index % 5 == 0:
                df.to_excel(f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx", index=False)

    except KeyboardInterrupt:
        print("\nStop paksa.")
    finally:
        df.to_excel(f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx", index=False)
        driver.quit()
        print("Selesai.")

if __name__ == "__main__":
    main_price_scraper()