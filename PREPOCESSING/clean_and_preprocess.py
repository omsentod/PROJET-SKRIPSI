import os
import pandas as pd
import numpy as np

# Konfigurasi Path Direktori
BASE_DIR = "/Users/macbookpro/Documents/GITHUB/PROJET-SKRIPSI/PREPOCESSING"
DATA_DIR = os.path.join(BASE_DIR, "DATA&HTM-NEW")

# File Inputs
HOTEL_FILE = os.path.join(DATA_DIR, "hotelV2-htm.xlsx")
KULINER_FILE = os.path.join(DATA_DIR, "tempat_makanV2-htm.xlsx")
WISATA_FILE = os.path.join(DATA_DIR, "wisataV2_updated.xlsx")

# File Outputs
HOTEL_OUT = os.path.join(BASE_DIR, "hotel_clean.xlsx")
KULINER_OUT = os.path.join(BASE_DIR, "tempat_makan_clean.xlsx")
WISATA_OUT = os.path.join(BASE_DIR, "wisata_clean.xlsx")
MASTER_OUT = os.path.join(BASE_DIR, "master_dataset_clean.xlsx")

def detect_and_handle_outliers(df, category_name):
    """
    Mendeteksi outlier harga menggunakan metode Interquartile Range (IQR).
    Untuk pariwisata, outlier harga sangat tinggi dieliminasi agar tidak mendistorsi klaster FCM.
    """
    prices = df['Estimasi_Harga'].dropna()
    if len(prices) == 0:
        return df, 0, 0, 0
    
    Q1 = np.percentile(prices, 25)
    Q3 = np.percentile(prices, 75)
    IQR = Q3 - Q1
    
    # Batas atas pencilan (outliers)
    upper_bound = Q3 + 1.5 * IQR
    lower_bound = max(0, Q1 - 1.5 * IQR)
    
    # Deteksi outliers
    outliers = df[df['Estimasi_Harga'] > upper_bound]
    num_outliers = len(outliers)
    
    # Bersihkan outlier (hanya membuang harga ekstrem atas)
    df_cleaned = df[df['Estimasi_Harga'] <= upper_bound]
    
    print(f"\n[OUTLIER - {category_name.upper()}]")
    print(f"   -> Q1 (25%): Rp {int(Q1):,}")
    print(f"   -> Q3 (75%): Rp {int(Q3):,}")
    print(f"   -> IQR: Rp {int(IQR):,}")
    print(f"   -> Batas Atas Outlier: Rp {int(upper_bound):,}")
    print(f"   -> Jumlah Outlier Ditemukan: {num_outliers} baris")
    if num_outliers > 0:
        print("   -> Contoh data pencilan yang dibuang:")
        for idx, row in outliers.head(3).iterrows():
            print(f"      * {row['Nama_Tempat']} (Rp {int(row['Estimasi_Harga']):,})")
            
    return df_cleaned, Q1, Q3, upper_bound

def preprocess_pipeline():
    print("="*80)
    print("🚀 MEMULAI PIPELINE PREPROCESSING DATA SKRIPSI")
    print("="*80)
    
    # -------------------------------------------------------------------------
    # 1. PROCESS HOTEL DATA
    # -------------------------------------------------------------------------
    print("\n[1/3] Memproses Dataset Hotel...")
    df_hotel = pd.read_excel(HOTEL_FILE)
    initial_hotel_len = len(df_hotel)
    
    # A. Duplikasi
    df_hotel = df_hotel.drop_duplicates(subset=['Nama_Tempat'], keep='first')
    dup_hotel = initial_hotel_len - len(df_hotel)
    
    # B. Missing Price (Hotel tidak boleh gratis atau kosong)
    df_hotel = df_hotel.dropna(subset=['Estimasi_Harga'])
    df_hotel = df_hotel[df_hotel['Estimasi_Harga'] > 0]
    missing_hotel = initial_hotel_len - dup_hotel - len(df_hotel)
    
    # C. Outliers
    df_hotel_clean, _, _, _ = detect_and_handle_outliers(df_hotel, "Hotel")
    outliers_hotel = len(df_hotel) - len(df_hotel_clean)
    
    # Save cleaned detail hotel
    df_hotel_clean.to_excel(HOTEL_OUT, index=False)
    
    # Create standard vector representation
    hotel_vector = df_hotel_clean[['Nama_Tempat', 'Latitude', 'Longitude', 'Estimasi_Harga']].copy()
    hotel_vector['Kategori'] = 'hotel'
    
    # -------------------------------------------------------------------------
    # 2. PROCESS KULINER DATA
    # -------------------------------------------------------------------------
    print("\n[2/3] Memproses Dataset Kuliner...")
    df_kuliner = pd.read_excel(KULINER_FILE)
    initial_kuliner_len = len(df_kuliner)
    
    # A. Duplikasi
    df_kuliner = df_kuliner.drop_duplicates(subset=['Nama_Tempat'], keep='first')
    dup_kuliner = initial_kuliner_len - len(df_kuliner)
    
    # B. Missing Price (Tempat makan tidak boleh gratis atau kosong)
    df_kuliner = df_kuliner.dropna(subset=['Estimasi_Harga'])
    df_kuliner = df_kuliner[df_kuliner['Estimasi_Harga'] > 0]
    missing_kuliner = initial_kuliner_len - dup_kuliner - len(df_kuliner)
    
    # C. Outliers
    df_kuliner_clean, _, _, _ = detect_and_handle_outliers(df_kuliner, "Kuliner")
    outliers_kuliner = len(df_kuliner) - len(df_kuliner_clean)
    
    # Save cleaned detail kuliner
    df_kuliner_clean.to_excel(KULINER_OUT, index=False)
    
    # Create standard vector representation
    kuliner_vector = df_kuliner_clean[['Nama_Tempat', 'Latitude', 'Longitude', 'Estimasi_Harga']].copy()
    kuliner_vector['Kategori'] = 'tempat makan'
    
    # -------------------------------------------------------------------------
    # 3. PROCESS WISATA DATA
    # -------------------------------------------------------------------------
    print("\n[3/3] Memproses Dataset Wisata...")
    df_wisata = pd.read_excel(WISATA_FILE)
    initial_wisata_len = len(df_wisata)
    
    # A. Duplikasi
    df_wisata = df_wisata.drop_duplicates(subset=['Nama_Tempat'], keep='first')
    dup_wisata = initial_wisata_len - len(df_wisata)
    
    # B. Missing Price (Wisata BOLEH gratis >= 0, tapi tidak boleh NaN)
    df_wisata = df_wisata.dropna(subset=['Estimasi_Harga'])
    df_wisata = df_wisata[df_wisata['Estimasi_Harga'] >= 0]
    missing_wisata = initial_wisata_len - dup_wisata - len(df_wisata)
    
    # C. Outliers
    df_wisata_clean, _, _, _ = detect_and_handle_outliers(df_wisata, "Wisata")
    outliers_wisata = len(df_wisata) - len(df_wisata_clean)
    
    # Save cleaned detail wisata
    df_wisata_clean.to_excel(WISATA_OUT, index=False)
    
    # Create standard vector representation
    wisata_vector = df_wisata_clean[['Nama_Tempat', 'Latitude', 'Longitude', 'Estimasi_Harga']].copy()
    wisata_vector['Kategori'] = 'wisata'
    
    # -------------------------------------------------------------------------
    # 4. MERGE DATASETS INTO UNIFIED VECTOR SPACE
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("🔗 PENGGABUNGAN DATA (CONCATENATION & VECTOR STANDARDIZATION)")
    print("="*80)
    
    master_df = pd.concat([hotel_vector, kuliner_vector, wisata_vector], ignore_index=True)
    
    # Pastikan koordinat berupa Float dan Harga berupa Integer murni
    master_df['Latitude'] = master_df['Latitude'].astype(float)
    master_df['Longitude'] = master_df['Longitude'].astype(float)
    master_df['Estimasi_Harga'] = master_df['Estimasi_Harga'].astype(int)
    
    # Urutkan ID secara terstruktur
    master_df.insert(0, 'Id_Tempat', range(1, len(master_df) + 1))
    
    # Simpan master dataset
    master_df.to_excel(MASTER_OUT, index=False)
    
    # -------------------------------------------------------------------------
    # 5. LAPORAN RINGKASAN AKADEMIS
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("📊 LAPORAN RINGKASAN PREPROCESSING DATA")
    print("="*80)
    print(f"{'Kategori':<15} | {'Data Awal':<10} | {'Duplikat':<10} | {'Missing Price':<15} | {'Outlier Dibuang':<15} | {'Data Bersih':<10}")
    print("-"*80)
    print(f"{'Hotel':<15} | {initial_hotel_len:<10} | {dup_hotel:<10} | {missing_hotel:<15} | {outliers_hotel:<15} | {len(df_hotel_clean):<10}")
    print(f"{'Tempat Makan':<15} | {initial_kuliner_len:<10} | {dup_kuliner:<10} | {missing_kuliner:<15} | {outliers_kuliner:<15} | {len(df_kuliner_clean):<10}")
    print(f"{'Wisata':<15} | {initial_wisata_len:<10} | {dup_wisata:<10} | {missing_wisata:<15} | {outliers_wisata:<15} | {len(df_wisata_clean):<10}")
    print("-"*80)
    print(f"{'TOTAL MASTER':<15} | {initial_hotel_len+initial_kuliner_len+initial_wisata_len:<10} | {dup_hotel+dup_kuliner+dup_wisata:<10} | {missing_hotel+missing_kuliner+missing_wisata:<15} | {outliers_hotel+outliers_kuliner+outliers_wisata:<15} | {len(master_df):<10}")
    print("="*80)
    print(f"✓ Master dataset berhasil disatukan di: {MASTER_OUT}")
    print(f"✓ File detail bersih tersimpan di folder PREPOCESSING.")
    print("="*80 + "\n")

if __name__ == "__main__":
    preprocess_pipeline()
