import pandas as pd
import glob
import os

def merge_and_clean_excel(folder_path, output_filename, duplicate_column):
    # 1. Cari semua file .xlsx di folder yang ditentukan
    all_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    
    if not all_files:
        print("Tidak ada file Excel (.xlsx) yang ditemukan di folder tersebut.")
        return

    print(f"Ditemukan {len(all_files)} file. Sedang memproses...")

    # 2. Baca setiap file dan masukkan ke dalam list
    df_list = []
    for filename in all_files:
        try:
            df = pd.read_excel(filename)
            df_list.append(df)
        except Exception as e:
            print(f"Gagal membaca file {filename}: {e}")

    # 3. Gabungkan semua data (Merge)
    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        print(f"Total baris sebelum dihapus duplikat: {len(merged_df)}")
        
        # Cek apakah kolom target ada
        if duplicate_column in merged_df.columns:
            # 4. Hapus Duplikat
            # keep='first' artinya menyimpan data pertama yang ditemukan dan menghapus sisanya
            cleaned_df = merged_df.drop_duplicates(subset=[duplicate_column], keep='first')
            
            print(f"Total baris setelah dihapus duplikat: {len(cleaned_df)}")
            print(f"Jumlah data duplikat yang dibuang: {len(merged_df) - len(cleaned_df)}")
            
            # 5. Simpan ke file baru
            cleaned_df.to_excel(output_filename, index=False)
            print(f"File berhasil disimpan: {output_filename}")
        else:
            print(f"Error: Kolom '{duplicate_column}' tidak ditemukan dalam data.")
            print("Kolom yang tersedia:", list(merged_df.columns))
    else:
        print("Tidak ada data yang berhasil digabungkan.")

# --- KONFIGURASI ---
# Ganti dengan nama kolom tempat di file excel Anda (misal: 'Place Name' atau 'Nama Tempat')
nama_kolom_target = 'Nama_Tempat'

# Jalankan fungsi (titik '.' berarti folder saat ini)
merge_and_clean_excel('.', 'merge-wisata.xlsx', nama_kolom_target)