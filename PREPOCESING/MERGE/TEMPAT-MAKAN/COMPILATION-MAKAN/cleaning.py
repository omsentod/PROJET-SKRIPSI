import pandas as pd
import numpy as np
import os

# ================= KONFIGURASI =================
INPUT_FILE = 'merge-makan.xlsx'
OUTPUT_FILE = 'merge-makan_cleaned.xlsx'
REMOVED_FILE = 'data_merge_makan_dibuang.xlsx'

# Daftar kata kunci blacklist (Surabaya dan sekitarnya)
BLACKLIST_KEYWORDS = [
    "Asemrowo", "Bubutan", "Bulak", "Dukuh Pakis", "Gubeng", "Genteng",
    "Gunung Anyar", "Jambangan", "Krembangan", "Kenjeran", "Lakarsantri",
    "Mulyorejo", "Pabean Cantikan", "Rungkut", "Semampir", "Sawahan",
    "Sukolilo", "Sukomanunggal", "Surabaya Barat", "Surabaya Selatan",
    "Surabaya Timur", "Surabaya Utara", "Taman", "Tegalsari", "Wonokromo",
    "Wiyung", "Simokerto", "Tambaksari", "Surabaya"
]

def clean_data():
    # Cek apakah file ada
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] File '{INPUT_FILE}' tidak ditemukan di folder ini.")
        return

    try:
        print(f"Sedang membaca file {INPUT_FILE}...")
        df = pd.read_excel(INPUT_FILE)
        initial_count = len(df)
        print(f"-> Jumlah data awal: {initial_count}")

        # --- 1. DETEKSI KOLOM OTOMATIS ---
        # Mencari kolom Latitude (biasanya mengandung kata 'lat')
        lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
        
        # Mencari kolom Teks untuk disearch (Nama Hotel, Alamat, Kota)
        # Kita ambil kolom bertipe object (string)
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        print(f"-> Kolom Latitude terdeteksi: {lat_col if lat_col else 'TIDAK DITEMUKAN'}")
        print(f"-> Kolom Teks yang diperiksa: {text_cols}")

        # --- 2. FILTER BERDASARKAN KATA KUNCI (TEXT) ---
        print("\nMelakukan filter kata kunci...")
        pattern = '|'.join(BLACKLIST_KEYWORDS)
        
        # Masker awal (False semua)
        mask_blacklist = pd.Series(False, index=df.index)
        
        for col in text_cols:
            # Cek keyword di setiap kolom teks, case=False agar tidak peduli huruf besar/kecil
            mask_blacklist |= df[col].astype(str).str.contains(pattern, case=False, na=False)

        print(f"-> Ditemukan {mask_blacklist.sum()} data mengandung kata kunci terlarang.")

        # --- 3. FILTER BERDASARKAN KOORDINAT (LATITUDE) ---
        mask_geo = pd.Series(False, index=df.index)
        if lat_col:
            print("\nMelakukan filter koordinat...")
            # Pastikan latitude berupa angka
            df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
            
            # LOGIKA: Surabaya/Sidoarjo Latitude > -7.55 (Mendekati 0)
            # Malang Latitude < -7.55 (Mendekati -8 atau -9)
            mask_geo = (df[lat_col] > -7.55) & (df[lat_col].notna())
            
            print(f"-> Ditemukan {mask_geo.sum()} data dengan posisi bukan di Malang (Latitude > -7.55).")

        # --- 4. EKSEKUSI PENGHAPUSAN ---
        # Gabungkan kedua filter (jika kena salah satu, hapus)
        mask_remove = mask_blacklist | mask_geo
        
        df_removed = df[mask_remove]
        df_clean = df[~mask_remove]

        # --- 5. SIMPAN HASIL ---
        print(f"\n=== HASIL AKHIR ===")
        print(f"Total data dihapus : {len(df_removed)}")
        print(f"Sisa data bersih   : {len(df_clean)}")

        df_clean.to_excel(OUTPUT_FILE, index=False)
        print(f"\n[SUKSES] File bersih disimpan sebagai: {OUTPUT_FILE}")
        
        if len(df_removed) > 0:
            df_removed.to_excel(REMOVED_FILE, index=False)
            print(f"[INFO] Data yang dihapus disimpan di : {REMOVED_FILE} (untuk pengecekan)")

    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")

if __name__ == "__main__":
    clean_data()