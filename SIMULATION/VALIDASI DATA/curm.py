import pdfplumber
import pandas as pd
import os

def extract_and_clean_pdf(pdf_path):
    """
    Membaca PDF dan mengubah semua tabel di dalamnya menjadi
    satu DataFrame Pandas yang rapi.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' tidak ditemukan.")
        return None

    all_data = []
    
    print("Sedang membaca data dari PDF... Mohon tunggu sebentar.")
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Ekstrak tabel dari halaman
            table = page.extract_table()
            
            if table:
                for row in table:
                    # Bersihkan karakter newline (\n) dan None
                    cleaned_row = [cell.replace('\n', ' ') if cell else "" for cell in row]
                    
                    # Filter: Abaikan header berulang atau baris judul BLOK
                    # Asumsi: Header tabel mengandung kata "NOPOL"
                    if len(cleaned_row) > 2 and ("NOPOL" in str(cleaned_row[1]) or "NOPOL" in str(cleaned_row[2])):
                        continue
                    if "BLOK" in str(cleaned_row[0]):
                        continue

                    all_data.append(cleaned_row)

    # Nama kolom sesuai struktur PDF Anda
    columns = [
        "NO", "NOPOL FISIK", "NOPOL ERI", "MERK", 
        "JENIS KENDARAAN", "NAMA PEMILIK", "KOTA", "NOKA"
    ]
    
    df = pd.DataFrame(all_data)
    
    # Penyesuaian kolom jika jumlahnya pas
    if df.shape[1] == len(columns):
        df.columns = columns
    else:
        print(f"Peringatan: Struktur tabel bervariasi. Kolom mungkin tidak sesuai label.")

    return df

def search_data(df):
    """
    Fitur pencarian interaktif dengan MULTI-KEYWORD.
    """
    print("\n" + "="*60)
    print("      SISTEM PENCARIAN DATA RANMOR (MULTI-KEYWORD)")
    print("="*60)
    print("Tips: Masukkan beberapa kata dipisah spasi.")
    print("      Contoh: 'HONDA SURABAYA' -> Cari Honda di kota Surabaya")
    print("      Contoh: 'VARIO MERAH' -> Cari Vario yang warnanya Merah")
    
    while True:
        raw_input = input("\nMasukkan kata kunci (atau ketik 'exit' untuk keluar): ").strip()
        
        if raw_input.lower() == 'exit':
            print("Terima kasih. Program berhenti.")
            break
        
        if not raw_input:
            print("Kata kunci tidak boleh kosong.")
            continue

        # 1. Pecah input menjadi list kata kunci (berdasarkan spasi)
        keywords = raw_input.split()
        
        # 2. Mulai filter: Awalnya semua data dianggap True (masuk kriteria)
        # Kita akan mempersempitnya (AND logic)
        final_mask = pd.Series([True] * len(df))

        for word in keywords:
            # Cari kata 'word' di SELURUH kolom (case-insensitive)
            # mask_word akan bernilai True jika baris tersebut mengandung kata tersebut
            mask_word = df.astype(str).apply(
                lambda x: x.str.contains(word, case=False, na=False)
            ).any(axis=1)
            
            # Gabungkan dengan mask utama menggunakan logika AND (&)
            # Data harus memenuhi kriteria sebelumnya DAN kriteria kata ini
            final_mask = final_mask & mask_word

        results = df[final_mask]

        if not results.empty:
            print(f"\nDitemukan {len(results)} data cocok:\n")
            print(results.to_string(index=False))
        else:
            print(f"\nTidak ditemukan data yang mengandung kombinasi: {keywords}")

# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    # Pastikan nama file sesuai dengan file di folder Anda
    nama_file_pdf = "curanmor.pdf" 
    
    # Load Data Sekali Saja
    df_ranmor = extract_and_clean_pdf(nama_file_pdf)
    
    # Masuk ke Loop Pencarian
    if df_ranmor is not None and not df_ranmor.empty:
        search_data(df_ranmor)
    else:
        print("Gagal mengekstrak data.")