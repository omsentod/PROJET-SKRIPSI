import pandas as pd
import numpy as np
import re

# ==============================================================================
# KONFIGURASI FILE
# ==============================================================================
# Ganti nama file ini sesuai nama file Excel kamu
nama_file_input = 'DataWisataMalang.xlsx' 
nama_file_output = 'DataWisata_FIX.xlsx'

# ==============================================================================
# 1. FUNGSI PEMBERSIH (CLEANING LOGIC)
# ==============================================================================

def bersihkan_harga(str_harga, nama_tempat):
    """
    Mengubah format harga yang kotor menjadi integer (rupiah murni).
    Mengisi data kosong dengan estimasi cerdas.
    """
    # 1. Jika Kosong (NaN), Estimasi berdasarkan Nama Tempat
    if pd.isna(str_harga) or str_harga == '' or str(str_harga).strip() == '-':
        nama = str(nama_tempat).lower()
        if any(x in nama for x in ['pantai', 'coban', 'air terjun', 'sumber', 'bukit', 'goa']):
            return 15000  # Estimasi Murah (Alam)
        elif any(x in nama for x in ['park', 'museum', 'night', 'skyland', 'jatim', 'waterpark']):
            return 50000  # Estimasi Mahal (Buatan)
        elif 'alun' in nama or 'taman' in nama:
            return 0      # Gratis
        else:
            return 25000  # Default rata-rata

    # 2. Bersihkan Karakter (Rp, titik, spasi)
    clean = str(str_harga).replace('Rp', '').replace('.', '').replace(',', '').replace(' ', '')

    # 3. Menangani Range (Contoh: "25-50K" atau "1-25.000")
    if '–' in clean or '-' in clean:
        try:
            clean = clean.replace('K', '000') # Ubah 50K jadi 50000
            parts = re.split('–|-', clean)
            # Ambil angka saja
            angka1 = int(re.sub(r'\D', '', parts[0]))
            angka2 = int(re.sub(r'\D', '', parts[1]))
            
            # Fix jika ada range aneh (misal depan 0 atau 1)
            if angka1 < 100: angka1 = 0 
            
            return int((angka1 + angka2) / 2) # Ambil nilai tengah
        except:
            return 30000 # Default jika error parsing

    # 4. Menangani Simbol Dolar ($$)
    if '$' in clean:
        if '$$$' in clean: return 150000
        elif '$$' in clean: return 75000
        else: return 35000

    # 5. Menangani Plus (250000+)
    if '+' in clean:
        return int(re.sub(r'\D', '', clean))

    # 6. Angka Biasa
    try:
        return int(re.sub(r'\D', '', clean))
    except:
        return 25000

def bersihkan_kategori(str_kategori, nama_tempat):
    """
    Menstandarisasi kategori dan mengisi yang kosong (Auto-Tagging).
    """
    # 1. Mapping Kategori yang sudah ada agar seragam
    if pd.notna(str_kategori) and str_kategori != '':
        k = str(str_kategori).lower()
        if any(x in k for x in ['bar', 'kedai kopi', 'cafe', 'lounge']):
            return 'Hiburan'
        if any(x in k for x in ['depot', 'kuliner', 'restoran', 'warung', 'rumah makan']):
            return 'Kuliner'
        return str_kategori.title() # Rapikan huruf kapital
    
    # 2. Auto-Tagging jika Kosong (Berdasarkan Nama)
    nama = str(nama_tempat).lower()
    if any(x in nama for x in ['pantai', 'coban', 'air terjun', 'gunung', 'teh', 'sumber', 'bukit', 'pulau', 'lembah']):
        return 'Alam'
    elif any(x in nama for x in ['park', 'museum', 'night', 'skyland', 'alun', 'recreation', 'waterpark', 'desa wisata']):
        return 'Buatan'
    elif any(x in nama for x in ['candi', 'heritage', 'kampung']):
        return 'Budaya'
    else:
        return 'Buatan' # Default fallback

def bersihkan_ulasan(str_ulasan):
    """
    Mengubah '(7,5 rb)' menjadi integer 7500.
    """
    if pd.isna(str_ulasan): return 0
    
    # Hapus kurung dan spasi
    clean = str(str_ulasan).replace('(', '').replace(')', '').replace(' ', '').replace(',', '.').lower()
    
    # Tangani minus (kadang ada data -632)
    clean = clean.replace('-', '')
    
    faktor = 1
    if 'rb' in clean or 'k' in clean:
        faktor = 1000
        clean = clean.replace('rb', '').replace('k', '')
        
    try:
        return int(float(clean) * faktor)
    except:
        return 0

# ==============================================================================
# 2. EKSEKUSI PROGRAM
# ==============================================================================

print("Sedang membaca file Excel...")
try:
    df = pd.read_excel(nama_file_input)
    print(f"Berhasil memuat {len(df)} data.")
except FileNotFoundError:
    print(f"ERROR: File '{nama_file_input}' tidak ditemukan. Pastikan nama file benar.")
    exit()

print("Sedang membersihkan data...")

# A. Cleaning Harga
# (Kita buat kolom baru 'Htm_Bersih' agar data asli tidak hilang untuk perbandingan)
df['Htm_Bersih'] = df.apply(lambda x: bersihkan_harga(x['Htm'], x['Nama_Tempat']), axis=1)

# B. Cleaning Kategori
df['Kategori_Bersih'] = df.apply(lambda x: bersihkan_kategori(x['Kategori'], x['Nama_Tempat']), axis=1)

# C. Cleaning Rating (Ganti koma jadi titik)
# Pastikan tipe data string dulu baru replace
df['Rating_Bersih'] = df['Rating'].astype(str).str.replace(',', '.').apply(lambda x: float(x) if x.replace('.','').isdigit() else 4.0)

# D. Cleaning Jumlah Ulasan
df['Ulasan_Bersih'] = df['Jumlah Ulasan'].apply(bersihkan_ulasan)

# ==============================================================================
# 3. EXPORT KE EXCEL BARU
# ==============================================================================

# Kita hanya ambil kolom yang bersih untuk file output
df_final = df[['Id_Tempat', 'Nama_Tempat', 'Rating_Bersih', 'Ulasan_Bersih', 'Kategori_Bersih', 'Htm_Bersih']]

# Rename kolom agar lebih rapi di database nanti
df_final.columns = ['id', 'nama', 'rating', 'jumlah_ulasan', 'kategori', 'harga_tiket']

print(f"Sedang menyimpan ke '{nama_file_output}'...")
df_final.to_excel(nama_file_output, index=False)

print("\n" + "="*50)
print("PROSES SELESAI!")
print("="*50)
print(f"Data bersih telah disimpan di: {nama_file_output}")
print("Contoh 5 data teratas:")
print(df_final.head())