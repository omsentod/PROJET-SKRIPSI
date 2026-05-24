import pandas as pd
import os

def min_max_normalization(filename, output_filename):
    print(f"🔄 Sedang menormalisasi file: {filename} ...")
    
    # Cek apakah file ada
    if not os.path.exists(filename):
        print(f"❌ File {filename} tidak ditemukan. Lewati.\n")
        return

    try:
        # 1. BACA FILE EXCEL
        df = pd.read_excel(filename)
        
        # 2. TENTUKAN KOLOM YANG MAU DINORMALISASI
        # Sesuaikan nama kolom ini dengan Excel Anda persis (Case Sensitive)
        target_cols = ['Estimasi_Harga', 'Latitude', 'Longitude']
        
        # Cek apakah kolom-kolom tersebut ada di file
        for col in target_cols:
            if col not in df.columns:
                print(f"⚠️ Peringatan: Kolom '{col}' tidak ditemukan di {filename}. Normalisasi kolom ini dilewati.")
                continue
            
            # 3. RUMUS MIN-MAX: (x - min) / (max - min)
            min_val = df[col].min()
            max_val = df[col].max()
            
            # Hindari pembagian dengan 0 jika datanya seragam (max == min)
            if max_val - min_val == 0:
                df[f'Norm_{col}'] = 0
            else:
                df[f'Norm_{col}'] = (df[col] - min_val) / (max_val - min_val)

        # 4. SIMPAN KE FILE BARU
        df.to_excel(output_filename, index=False)
        print(f"✅ Berhasil! Data normalisasi disimpan di: {output_filename}\n")

    except Exception as e:
        print(f"❌ Terjadi Error pada {filename}: {e}\n")

# ==========================================================
# EKSEKUSI UNTUK 3 DATASET
# ==========================================================

# Format: min_max_normalization('nama_file_asli.xlsx', 'nama_file_hasil.xlsx')

# 1. Dataset Wisata
min_max_normalization('dbset-norm/wisata.xlsx', 'wisata_normalized.xlsx')

# 2. Dataset Hotel
min_max_normalization('dbset-norm/hotel.xlsx', 'hotel_normalized.xlsx')

# 3. Dataset Tempat Makan
# Perhatikan nama file (apakah pakai strip '-' atau underscore '_')
min_max_normalization('dbset-norm/tempat-makan.xlsx', 'makan_normalized.xlsx')