import pandas as pd
import time
import re
import random
import os
import requests
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ================= KONFIGURASI FOLDER =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAMBAR_DIR = os.path.join(BASE_DIR, 'GAMBAR')

# Pemetaan kategori ke file input dan subfolder output
KATEGORI_CONFIG = {
    '1': {
        'name': 'wisata',
        'file': 'GAMBAR/wisataV2.xlsx',
        'subfolder': 'wisata'
    },
    '2': {
        'name': 'makan',
        'file': 'GAMBAR/tempat_makanV2.xlsx',
        'subfolder': 'makan'
    },
    '3': {
        'name': 'hotel',
        
        'file': 'GAMBAR/hotelv2.xlsx',
        'subfolder': 'hotel'
    }
}
# ======================================================

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(45)
    return driver

def clean_filename(name):
    """Membersihkan nama tempat agar aman digunakan sebagai nama file/folder."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = cleaned.replace(" ", "_") # Ganti spasi dengan underscore agar rapi di file sistem
    return cleaned.strip()

def bypass_consent(driver):
    """Melewati popup cookie / persetujuan Google jika muncul."""
    try:
        consent_buttons = driver.find_elements(By.XPATH, "//button[span[contains(text(), 'Tolak semua') or contains(text(), 'Reject all') or contains(text(), 'Saya setuju') or contains(text(), 'Agree')]]")
        for btn in consent_buttons:
            if btn.is_displayed():
                btn.click()
                print("   -> ✓ Berhasil melewati popup consent Google!")
                time.sleep(2)
                break
    except:
        pass

def open_photo_gallery(driver, wait):
    """Membuka panel galeri foto dengan mencoba berbagai macam selector."""
    selectors = [
        "button[jsaction*='pane.heroHeader']",
        "button[aria-label^='Foto']",
        "button[aria-label^='Photo']",
        "div[class*='hero'] button",
        "div.header-hero img"
    ]
    
    for sel in selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            print(f"   -> ✓ Galeri foto terbuka menggunakan selector: {sel}")
            return True
        except Exception:
            try:
                # Coba via JavaScript jika standard click gagal
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                driver.execute_script("arguments[0].click();", btn)
                print(f"   -> ✓ Galeri foto terbuka via JS: {sel}")
                return True
            except Exception:
                continue
                
    # Fallback menggunakan XPath umum yang mencari kata 'Foto' atau 'Photo'
    try:
        btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Foto') or contains(@aria-label, 'Photo')]")
        driver.execute_script("arguments[0].click();", btn)
        print("   -> ✓ Galeri foto terbuka via XPath Fallback")
        return True
    except:
        pass
        
    return False

def get_gallery_images(driver, limit=5):
    """Mengambil URL gambar unik dari galeri foto dan mengubah ke resolusi tinggi."""
    image_urls = []
    
    # Mencari container scroll galeri agar bisa lazy-load gambar
    scrollable_selectors = [
        "div[role='feed']",
        "div.m6t5gc-tl1oF-Hj5ED",
        "div[tabindex='0'].section-layout",
        "div.D42Z1c"
    ]
    
    scrollable_div = None
    for sel in scrollable_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                scrollable_div = el
                break
        except:
            continue
            
    # Lakukan scrolling beberapa kali agar elemen gambar termuat
    for scroll_idx in range(6):
        imgs = driver.find_elements(By.TAG_NAME, "img")
        for img in imgs:
            try:
                src = img.get_attribute("src")
                if src and ("googleusercontent.com" in src or "streetviewpixels" in src):
                    # Filter out foto profil pengguna (kecil, ada /a/ atau ukuran kecil)
                    if "/a/" in src or "=s36" in src or "=s40" in src or "=s44" in src or "=s48" in src or "=s64" in src:
                        continue
                    
                    # Konversi parameter ukuran ke resolusi tinggi (=w1080)
                    if '=' in src:
                        base_url = src.split('=')[0]
                        high_res = base_url + "=w1080"
                    else:
                        high_res = src
                        
                    if high_res not in image_urls:
                        image_urls.append(high_res)
                        if len(image_urls) >= limit:
                            return image_urls
            except Exception:
                continue
                
        # Scroll container ke bawah
        if scrollable_div:
            try:
                driver.execute_script("arguments[0].scrollBy(0, 450);", scrollable_div)
            except:
                pass
        else:
            try:
                driver.execute_script("window.scrollBy(0, 450);")
            except:
                pass
        time.sleep(1.5)
        
    return image_urls

def download_image(url, save_path):
    """Mengunduh gambar dari URL dan menyimpannya ke local."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"      ✗ Gagal download {os.path.basename(save_path)}: {e}")
    return False

def main_image_scraper():
    print("="*65)
    print("        🚀 GOOGLE MAPS IMAGE SCRAPER - PREMIUM & AUTO-RESUME 🚀")
    print("="*65)
    print("Pilih Kategori yang ingin Anda download gambarnya:")
    print("1. Tempat Wisata (wisata)")
    print("2. Tempat Makan (makan)")
    print("3. Hotel (hotel)")
    
    pilihan = input("Masukkan nomor pilihan (1/2/3): ").strip()
    if pilihan not in KATEGORI_CONFIG:
        print("✗ Pilihan tidak valid! Program keluar.")
        return
        
    config = KATEGORI_CONFIG[pilihan]
    file_input = config['file']
    subfolder_nama = config['subfolder']
    
    updated_filename = f"{file_input.replace('.xlsx', '')}_updated.xlsx"
    
    # Cek progress resume
    if os.path.exists(updated_filename):
        print("\n" + "="*60)
        print("🔄 DATA PROGRESS SEBELUMNYA DITEMUKAN!")
        print("="*60)
        pilihan_resume = input(f"Apakah Anda ingin MELANJUTKAN scraping dari '{updated_filename}'? (y/n): ").strip().lower()
        if pilihan_resume == 'y':
            file_to_load = updated_filename
            print("✓ Melanjutkan progress kemajuan sebelumnya...")
        else:
            file_to_load = file_input
            print("✓ Memulai dari awal (menggunakan file input mentah)...")
    else:
        file_to_load = file_input
        
    try:
        df = pd.read_excel(file_to_load)
    except Exception as e:
        print(f"✗ File '{file_to_load}' tidak dapat dimuat: {e}")
        return
        
    # Tambahkan kolom tracking gambar jika belum ada
    if 'Gambar_Terunduh' not in df.columns:
        df['Gambar_Terunduh'] = 0
    if 'Folder_Gambar' not in df.columns:
        df['Folder_Gambar'] = ''

    # Buat direktori output utama jika belum ada
    kategori_dir = os.path.join(GAMBAR_DIR, subfolder_nama)
    os.makedirs(kategori_dir, exist_ok=True)
    
    print(f"\n📁 Lokasi Penyimpanan : {kategori_dir}")
    print(f"📊 Total Data Tempat   : {len(df)}")
    print("Membuka browser Chrome...")
    
    driver = init_driver()
    wait = WebDriverWait(driver, 15)
    
    success_places = 0
    total_images_downloaded = 0
    searches_since_restart = 0
    
    try:
        for index, row in df.iterrows():
            nama_tempat = row['Nama_Tempat']
            link_maps = row['Link']
            
            # Bersihkan nama tempat untuk folder dan file
            nama_bersih = clean_filename(nama_tempat)
            folder_tempat = os.path.join(kategori_dir, nama_bersih)
            
            # Cek apakah folder sudah memiliki minimal 5 gambar
            existing_images = []
            if os.path.exists(folder_tempat):
                existing_images = [f for f in os.listdir(folder_tempat) if f.lower().endswith('.jpg')]
                
            if len(existing_images) >= 5 and pd.notna(row['Gambar_Terunduh']) and row['Gambar_Terunduh'] >= 5:
                print(f"\n[{index+1}/{len(df)}] Skip '{nama_tempat}' (Sudah memiliki {len(existing_images)} gambar).")
                continue
                
            # Jika link kosong, skip
            if pd.isna(link_maps) or not str(link_maps).startswith("http"):
                print(f"\n[{index+1}/{len(df)}] Skip '{nama_tempat}' (Tautan tidak valid).")
                continue
                
            # Restart browser berkala setiap 10 tempat agar memori bersih
            if searches_since_restart > 0 and searches_since_restart % 10 == 0:
                print("\n🔄 Merestart browser Chrome secara berkala untuk menjaga stabilitas...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(2)
                driver = init_driver()
                wait = WebDriverWait(driver, 15)
                searches_since_restart = 0
                
            searches_since_restart += 1
            print(f"\n[{index+1}/{len(df)}] Memproses: '{nama_tempat}'")
            
            try:
                driver.get(link_maps)
                time.sleep(4)
                bypass_consent(driver)
                
                # Buka galeri foto
                galeri_terbuka = open_photo_gallery(driver, wait)
                if not galeri_terbuka:
                    print("   -> ✗ Tidak dapat menemukan tombol galeri foto. Mencoba cari di seluruh halaman...")
                    
                time.sleep(3)
                
                # Ekstrak URL gambar
                image_urls = get_gallery_images(driver, limit=5)
                print(f"   -> ✓ Ditemukan {len(image_urls)} gambar di galeri.")
                
                if image_urls:
                    os.makedirs(folder_tempat, exist_ok=True)
                    downloaded_count = 0
                    
                    for i, img_url in enumerate(image_urls):
                        file_name = f"{nama_bersih}-{i+1}.jpg"
                        save_path = os.path.join(folder_tempat, file_name)
                        
                        success = download_image(img_url, save_path)
                        if success:
                            downloaded_count += 1
                            total_images_downloaded += 1
                            
                    print(f"   -> ✓ Berhasil mengunduh {downloaded_count} gambar.")
                    df.at[index, 'Gambar_Terunduh'] = downloaded_count
                    df.at[index, 'Folder_Gambar'] = os.path.relpath(folder_tempat, BASE_DIR)
                    success_places += 1
                else:
                    print("   -> ✗ Gagal menemukan gambar apa pun.")
                    df.at[index, 'Gambar_Terunduh'] = 0
                    
            except Exception as e:
                print(f"   -> ✗ Error saat memproses tempat ini: {e}")
                df.at[index, 'Gambar_Terunduh'] = 0
                
            # Jeda acak manusiawi
            time.sleep(random.uniform(4, 7))
            
            # Simpan kemajuan setiap 3 baris
            if (index + 1) % 3 == 0:
                df.to_excel(updated_filename, index=False)
                print(f"💾 Progress sementara aman tersimpan di: {updated_filename}")
                
    except KeyboardInterrupt:
        print("\n🛑 Proses dihentikan secara paksa oleh Pengguna!")
    finally:
        df.to_excel(updated_filename, index=False)
        try:
            driver.quit()
        except:
            pass
            
        print("\n" + "="*65)
        print("✓ SELESAI PENUH / KELUAR DARI PROSES")
        print(f"Total Tempat Diproses  : {success_places}")
        print(f"Total Gambar Diunduh   : {total_images_downloaded}")
        print(f"Seluruh data progress disimpan aman di: {updated_filename}")
        print("="*65 + "\n")

if __name__ == "__main__":
    main_image_scraper()
