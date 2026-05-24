import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# ==============================================================================
# FUNGSI BANTUAN
# ==============================================================================
def get_lat_long_from_url(url):
    if not url: return None, None
    try:
        coords = re.search(r'!3d([-0-9.]+)!4d([-0-9.]+)', url)
        if coords:
            return coords.group(1), coords.group(2)
    except:
        return None, None
    return None, None

def clean_rating_advanced(element):
    """Mengambil rating dengan aman. Jika gagal, return 0."""
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

def extract_price_strict(full_text_list):
    """Mencari harga. Jika gagal, return 0."""
    try:
        for line in full_text_list:
            if "Rp" in line:
                clean = re.sub(r'[^\d]', '', line)
                if clean: return int(clean)
    except:
        pass
    return 0

def extract_category_safe(full_text_list):
    """Mencari kategori. Default 'Wisata Umum'."""
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

# ==============================================================================
# IMPROVED SCROLLING FUNCTION
# ==============================================================================
def scroll_google_maps_feed(driver, max_scrolls=100):
    """
    Scroll feed Google Maps sampai benar-benar mentok.
    
    Improvements:
    - Mendeteksi "You've reached the end" message
    - Scroll lebih lambat dengan jeda render
    - Menghitung stagnasi scroll yang lebih akurat
    - Menangani lazy loading
    """
    try:
        # Tunggu feed muncul dengan timeout lebih lama
        wait = WebDriverWait(driver, 15)
        scrollable_div = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
        )
        print("✓ Feed ditemukan, mulai scrolling...")
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        stagnant_count = 0  # Hitung berapa kali height tidak berubah
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            # Scroll ke bawah
            driver.execute_script(
                "arguments[0].scrollTo(0, arguments[0].scrollHeight);", 
                scrollable_div
            )
            
            # Tunggu lebih lama untuk render (PENTING!)
            time.sleep(2.5)  # Naikkan dari 1.5 detik
            
            # Cek apakah sudah sampai akhir dengan mencari pesan "end"
            try:
                # Google Maps menampilkan pesan berbeda tergantung bahasa
                end_messages = [
                    "You've reached the end of the list",
                    "Anda telah mencapai akhir daftar",
                    "Kamu sudah sampai di akhir"
                ]
                
                page_text = scrollable_div.text.lower()
                if any(msg.lower() in page_text for msg in end_messages):
                    print("\n✓ Mencapai akhir daftar (End message detected)")
                    break
            except:
                pass
            
            # Cek perubahan height
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            
            if new_height == last_height:
                stagnant_count += 1
                print(f"⚠ Stagnant {stagnant_count}/5", end=" ", flush=True)
                
                # Jika 5x berturut-turut tidak ada perubahan, stop
                if stagnant_count >= 5:
                    print("\n✓ Tidak ada data baru setelah 5 percobaan")
                    break
                    
                # Coba scroll sedikit ke atas lalu ke bawah lagi (trick untuk trigger lazy load)
                driver.execute_script("arguments[0].scrollBy(0, -100);", scrollable_div)
                time.sleep(0.5)
                driver.execute_script("arguments[0].scrollBy(0, 100);", scrollable_div)
                
            else:
                stagnant_count = 0  # Reset counter jika ada progress
                last_height = new_height
                print(".", end="", flush=True)
            
            scroll_count += 1
        
        print(f"\n✓ Scrolling selesai setelah {scroll_count} iterasi")
        
    except TimeoutException:
        print("✗ Timeout: Feed tidak ditemukan dalam 15 detik")
    except Exception as e:
        print(f"✗ Error saat scrolling: {e}")

# ==============================================================================
# MAIN SCRAPER (UPDATED)
# ==============================================================================
def scrape_google_maps_v8(keyword):
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")  # Buka fullscreen
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print(f"--- Memulai Scraping V8 (Enhanced): '{keyword}' ---")
        driver.get(f"https://www.google.com/maps/search/{keyword}")
        
        # PENTING: Tunggu halaman load dengan baik
        print("Menunggu halaman load...")
        time.sleep(12)  # Naikkan dari 5 detik
        
        # Panggil fungsi scrolling yang sudah diperbaiki
        scroll_google_maps_feed(driver, max_scrolls=100)
        
        print("\nMulai ekstraksi data...")
        
        # Ambil semua elemen kartu
        cards = driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
        print(f"Total elemen ditemukan: {len(cards)}")
        
        results = []
        for i, card in enumerate(cards):
            nama = "Tanpa Nama"
            url = ""
            lat, long = 0, 0
            rating, ulasan = "0", 0
            kategori = "Wisata Umum"
            harga = 0
            
            try:
                # 1. Ambil Link & Nama
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    url = link_el.get_attribute('href')
                    nama = link_el.get_attribute('aria-label')
                    if not nama: continue
                except:
                    continue
                
                # 2. Ambil Lat/Long
                lat, long = get_lat_long_from_url(url)
                
                # 3. Ambil Rating
                rating, ulasan = clean_rating_advanced(card)
                
                # 4. Ambil Teks untuk Kategori & Harga
                try:
                    full_text = card.text.split('\n')
                    kategori = extract_category_safe(full_text)
                    harga = extract_price_strict(full_text)
                except StaleElementReferenceException:
                    print(f"x", end="")
                    continue
                except:
                    pass
                
                results.append({
                    'Id_Tempat': len(results) + 1,
                    'Nama_Tempat': nama,
                    'Rating': rating,
                    'Jumlah_Ulasan': ulasan,
                    'Kategori': kategori,
                    'Harga_Tiket': harga,
                    'Latitude': lat,
                    'Longitude': long,
                    'Link': url
                })
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"\r⚙ Diproses: {i + 1}/{len(cards)}", end="", flush=True)
                
            except Exception as e:
                continue
        
        print(f"\n✓ Ekstraksi selesai!")
        return results
        
    except Exception as e:
        print(f"✗ Error Driver: {e}")
        return []
    finally:
        driver.quit()

# ================= EKSEKUSI =================
if __name__ == "__main__":
    keyword_input = input("Masukkan Kata Kunci: ")
    data = scrape_google_maps_v8(keyword_input)
    
    if data:
        df = pd.DataFrame(data)
        df.drop_duplicates(subset=['Nama_Tempat'], inplace=True)
        df['Id_Tempat'] = range(1, len(df) + 1)
        
        filename = f"{keyword_input.replace(' ', '_')}_Final_V8.xlsx"
        df.to_excel(filename, index=False)
        
        print(f"\n{'='*60}")
        print(f"✓ BERHASIL! {len(df)} data tersimpan di {filename}")
        print(f"{'='*60}")
        print("\nPreview Data:")
        print(df[['Nama_Tempat', 'Rating', 'Jumlah_Ulasan', 'Harga_Tiket']].head(10))
    else:
        print("✗ Data kosong.")