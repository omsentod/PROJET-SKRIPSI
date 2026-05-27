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
FILE_INPUT = 'wisataV2_updated.xlsx' 
KATEGORI = 'wisata' # 'wisata' atau 'hotel'
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

def extract_price_from_text(text):
    text_lower = text.lower()
    
    # 1. Cari kandidat harga non-nol terlebih dahulu
    pola_harga = r'(?:rp\.?|idr)\s?(\d{1,3}(?:[.,]\d{3})+(?:\d{3})?)'
    matches = re.finditer(pola_harga, text_lower)
    
    candidates = []
    for match in matches:
        harga_str = match.group(1).replace('.', '').replace(',', '')
        try:
            harga_int = int(harga_str)
            if 1000 <= harga_int <= 500000:  # Batas logis harga tiket masuk
                # Hitung skor berdasarkan kata kunci di sekitar harga tersebut
                start_idx = max(0, match.start() - 60)
                end_idx = min(len(text_lower), match.end() + 60)
                context = text_lower[start_idx:end_idx]
                
                score = 0
                if any(k in context for k in ["tiket masuk", "htm", "tiket", "tarif", "harga"]):
                    score += 10
                if "dewasa" in context or "umum" in context:
                    score += 5
                if "weekdays" in context or "hari kerja" in context or "senin" in context:
                    score += 3
                    
                # Sinyal negatif (kemungkinan bukan harga tiket masuk utama)
                if "parkir" in context:
                    score -= 8
                if "kamera" in context or "sewa" in context:
                    score -= 4
                if "anak" in context: # Harga anak biasanya sekunder setelah dewasa
                    score -= 2
                if "kamar" in context or "hotel" in context or "menginap" in context:
                    score -= 10
                
                # Tambahan: Periksa teks spesifik yang berada langsung setelah harga (jarak dekat)
                after_context = text_lower[match.end():match.end() + 30]
                if "anak" in after_context:
                    score -= 15 # Hukuman sangat berat jika setelah harga langsung ada kata "anak"
                if "dewasa" in after_context or "umum" in after_context:
                    score += 15 # Bonus sangat besar jika setelah harga langsung ada kata "dewasa"
                if "parkir" in after_context:
                    score -= 15 # Hukuman sangat berat jika harga ini adalah tarif parkir
                
                candidates.append((harga_int, score, match.start()))
        except ValueError:
            continue
            
    # 2. Cek apakah ada pernyataan "gratis" yang sangat spesifik untuk tiket masuk utama
    has_free_ticket = False
    free_keywords = ["gratis", "free", "tidak dipungut biaya", "tidak dikenakan biaya", "tanpa biaya", "sukarela"]
    for kw in free_keywords:
        if kw in text_lower:
            start_idx = text_lower.find(kw)
            # Gunakan window yang lebih lebar (150 karakter) karena AI Overview sering menyisipkan keterangan panjang di antara kata
            context = text_lower[max(0, start_idx - 150):min(len(text_lower), start_idx + 150)]
            # Pastikan kata kunci gratis merujuk ke tiket masuk, bukan hal sekunder
            if any(tk in context for tk in ["tiket", "masuk", "htm", "karcis", "kunjung", "wisata"]):
                if not any(neg in text_lower[max(0, start_idx - 15):start_idx] for neg in ["tidak", "bukan", "belum"]):
                    # Pastikan bukan gratisan parkir, toilet, wifi, kamera, atau untuk anak kecil saja
                    near_text = text_lower[max(0, start_idx - 30):start_idx + 30]
                    if not any(bad in near_text for bad in ["parkir", "toilet", "wifi", "kamera", "foto", "anak"]):
                        has_free_ticket = True
                        break
                        
    # 3. Keputusan Utama (Prioritaskan harga bayar yang sah daripada klausa gratis anak/fasilitas)
    if candidates:
        # Urutkan berdasarkan skor tertinggi
        candidates.sort(key=lambda x: (-x[1], x[2]))
        best_candidate = candidates[0]
        
        # Jika kandidat non-nol terbaik memiliki keyakinan positif (score >= 5),
        # maka tempat ini berbayar dan kita ambil harga ini!
        if best_candidate[1] >= 5:
            return best_candidate[0], False
            
        # Jika semua kandidat non-nol memiliki skor rendah/negatif,
        # tetapi ada pernyataan tiket masuk gratis yang kuat, kembalikan gratis (Rp 0)
        if has_free_ticket:
            return 0, True
            
        # Jika tidak ada konfirmasi gratis yang kuat, kembalikan saja kandidat terbaik tersebut
        return best_candidate[0], False
        
    # Jika tidak ada kandidat Rp/IDR, barulah kita kembalikan gratis jika terdeteksi
    if has_free_ticket:
        return 0, True
        
    # 4. Fallback jika tidak ada Rp/IDR tapi ada angka ribuan di dekat kata kunci tiket
    pola_angka = r'\b(\d{1,3}\.\d{3})\b'
    matches_angka = re.finditer(pola_angka, text_lower)
    candidates_angka = []
    for match in matches_angka:
        harga_str = match.group(1).replace('.', '')
        try:
            harga_int = int(harga_str)
            if 2000 <= harga_int <= 500000:
                start_idx = max(0, match.start() - 40)
                end_idx = min(len(text_lower), match.end() + 40)
                context = text_lower[start_idx:end_idx]
                
                if any(k in context for k in ["rp", "rupiah", "tiket", "htm", "tarif", "masuk"]):
                    score = 0
                    if any(k in context for k in ["tiket masuk", "htm"]):
                        score += 5
                    
                    # Cek konteks setelah angka untuk fallback juga
                    after_context = text_lower[match.end():match.end() + 30]
                    if "anak" in after_context:
                        score -= 15
                    if "dewasa" in after_context or "umum" in after_context:
                        score += 15
                    if "parkir" in after_context:
                        score -= 15
                        
                    candidates_angka.append((harga_int, score, match.start()))
        except ValueError:
            continue
            
    if candidates_angka:
        candidates_angka.sort(key=lambda x: (-x[1], x[2]))
        return candidates_angka[0][0], False
        
    return None, False

def find_sge_container(driver):
    search_texts = ["ringkasan ai", "ai overview", "ringkasan oleh ai", "ringkasan ai oleh google"]
    
    # Ambil elemen-elemen umum yang berpotensi menjadi tajuk AI Overview
    elements = driver.find_elements(By.XPATH, "//*[self::div or self::span or self::h1 or self::h2 or self::h3 or self::b or self::strong]")
    
    for el in elements:
        try:
            txt = el.text.lower()
            if any(st in txt for st in search_texts):
                if el.is_displayed():
                    # Naik ke atas untuk mencari kontainer pembungkus utama
                    parent = el
                    for _ in range(6): # Naik maksimal 6 tingkat
                        parent = parent.find_element(By.XPATH, "..")
                        p_text = parent.text
                        if len(p_text) > 100:
                            # Cari semua link di dalam kontainer ini
                            links = parent.find_elements(By.TAG_NAME, "a")
                            ext_links = []
                            for l in links:
                                href = l.get_attribute("href")
                                if href and href.startswith("http"):
                                    domain_parsed = urllib.parse.urlparse(href).netloc.lower()
                                    # Filter out all Google-owned system domains
                                    is_google = False
                                    for g_domain in ["google", "gstatic", "youtube"]:
                                        if g_domain in domain_parsed:
                                            is_google = True
                                            break
                                    if not is_google:
                                        ext_links.append(href)
                            if ext_links:
                                return parent, p_text, ext_links
        except:
            continue
    return None, "", []

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
        
        # 1. COBA EKSTRAK DARI GOOGLE AI OVERVIEW (SGE) DAHULU
        sge_container, sge_text, sge_links = find_sge_container(driver)
        if sge_container:
            print("\n   -> AI Overview terdeteksi! Mengekstrak data...", end="", flush=True)
            harga_int, is_free = extract_price_from_text(sge_text)
            if harga_int is not None:
                primary_link = sge_links[0]
                domain = urllib.parse.urlparse(primary_link).netloc.lower()
                clean_domain = domain[4:] if domain.startswith("www.") else domain
                # Langsung mengembalikan nama domain rujukan asli dari AI
                return harga_int, clean_domain, primary_link
        
        # 2. FALLBACK KE ORGANIC PENCARIAN GOOGLE JIKA SGE TIDAK ADA ATAU GAGAL
        headings = driver.find_elements(By.CSS_SELECTOR, "#rso h3")
        
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
                
                # Temukan container hasil pencarian untuk mengambil snippet teks
                try:
                    container = h3_el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'g') or @class='tF2Cxc' or @class='MjjYud'][1]")
                except:
                    container = h3_el.find_element(By.XPATH, "./../../..")
                
                text = container.text
                
                # Gunakan extract_price_from_text agar skoring cerdas juga berlaku pada hasil organik
                harga_int, is_free = extract_price_from_text(text)
                if harga_int is not None:
                    clean_domain = domain[4:] if domain.startswith("www.") else domain
                    return harga_int, clean_domain, link_url
            except:
                continue
                    
        return None, "N/A", ""
        
    except Exception as e:
        print(f"Error saat mengekstrak harga: {e}")
        return None, "N/A", ""

def main_price_scraper():
    updated_filename = f"{FILE_INPUT.replace('.xlsx', '')}_updated.xlsx"
    
    # Cek apakah ada data kemajuan sebelumnya untuk dilanjutkan (resume)
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

    # Inisialisasi kolom jika belum ada (ditambahkan kolom Link_Sumber untuk pembuktian sidang)
    if 'Estimasi_Harga' not in df.columns:
        df['Estimasi_Harga'] = pd.NA
    if 'Sumber_Data' not in df.columns:
        df['Sumber_Data'] = 'N/A'
    if 'Link_Sumber' not in df.columns:
        df['Link_Sumber'] = ''

    print("=== SCRAPER HARGA GOOGLE AKADEMIS & JEJAK AUDIT TAUTAN ===")
    print(f"File Input    : {FILE_INPUT}")
    print(f"Kategori      : {KATEGORI.upper()}")
    print("Membuka browser Chrome...")
    
    driver = init_driver()
    
    success_count = 0
    searches_since_restart = 0
    
    try:
        for index, row in df.iterrows():
            # HANYA memproses data yang saat ini terisi harga 0 atau kosong (NaN/Null)
            # untuk memverifikasi ulang apakah tempat wisata tersebut gratis atau sebenarnya berbayar!
            # Semua data harga berbayar lainnya (> 0) akan dilewati!
            estimasi = row.get('Estimasi_Harga', 0)
            
            should_process = False
            if pd.isna(estimasi) or estimasi is None or estimasi == '':
                should_process = True
            else:
                try:
                    price_val = int(estimasi)
                    if price_val == 0:
                        should_process = True
                except:
                    pass
            
            # Jika TIDAK masuk kriteria harga == 0 atau kosong, lewati!
            if not should_process:
                continue
                
            # Restart browser berkala setiap 15 pencarian agar memori bersih & terhindar dari block
            if searches_since_restart > 0 and searches_since_restart % 15 == 0:
                print("\n🔄 Merestart browser Chrome secara berkala untuk menjaga stabilitas...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(2)
                driver = init_driver()
                searches_since_restart = 0 # Reset counter
            
            # Tambahkan counter pencarian
            searches_since_restart += 1
            nama = row['Nama_Tempat']
            
            query = f"Harga tiket masuk {nama} Malang"
            
            print(f"\n[{index+1}/{len(df)}] Menelusuri {nama}:")
            print("   -> Mencoba Google Search... ", end="", flush=True)
            harga_ditemukan, domain_ditemukan, link_ditemukan = get_price_from_google(driver, query, None)
            
            if harga_ditemukan is not None:
                df.at[index, 'Estimasi_Harga'] = harga_ditemukan
                df.at[index, 'Sumber_Data'] = domain_ditemukan
                df.at[index, 'Link_Sumber'] = link_ditemukan
                success_count += 1
                if harga_ditemukan == 0:
                    print(f"Berhasil! (Gratis/Rp 0 via {domain_ditemukan})")
                else:
                    print(f"Berhasil! (Rp {harga_ditemukan:,} via {domain_ditemukan})")
            else:
                print("Nihil (Diatur ke NaN/Kosong karena tidak dapat diverifikasi)")
                df.at[index, 'Estimasi_Harga'] = pd.NA
                df.at[index, 'Sumber_Data'] = 'N/A'
                df.at[index, 'Link_Sumber'] = ''
            
            # Jeda manusiawi antar pencarian
            time.sleep(random.uniform(4, 7))
            
            # Auto-save berkala setiap 5 baris
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
        print(f"Total Data Harga Wisata Terkumpul: {success_count}")
        print(f"Seluruh data disimpan aman di: {updated_filename}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main_price_scraper()
