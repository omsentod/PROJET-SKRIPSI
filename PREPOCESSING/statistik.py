"""
cek_statistik.py — Ekstrak statistik final dari wisata_clean.xlsx
Jalankan di folder yang sama dengan wisata_clean.xlsx (BASE_DIR PREPOCESSING/).
"""
import pandas as pd

# ============================================================
# 1. STATISTIK HARGA WISATA
# ============================================================
df = pd.read_excel('wisata_clean.xlsx')

print("=" * 70)
print("KOLOM DATAFRAME wisata_clean.xlsx:")
print("=" * 70)
print(df.columns.tolist())

print("\n" + "=" * 70)
print("STATISTIK HARGA WISATA (Estimasi_Harga):")
print("=" * 70)
desc = df['Estimasi_Harga'].describe()
print(desc)

print("\n" + "=" * 70)
print("JUMLAH HARGA = 0 (wisata gratis):")
print("=" * 70)
n_gratis = (df['Estimasi_Harga'] == 0).sum()
print(f"  {n_gratis} record berharga 0")

print("\n" + "=" * 70)
print("5 RECORD WISATA DENGAN HARGA TERTINGGI:")
print("=" * 70)
top5 = df.nlargest(5, 'Estimasi_Harga')[['Nama_Tempat', 'Estimasi_Harga', 'Sumber_Data']]
print(top5.to_string(index=False))

print("\n" + "=" * 70)
print("5 RECORD WISATA DENGAN HARGA TERENDAH (di atas 0):")
print("=" * 70)
bot5 = df[df['Estimasi_Harga'] > 0].nsmallest(5, 'Estimasi_Harga')[['Nama_Tempat', 'Estimasi_Harga', 'Sumber_Data']]
print(bot5.to_string(index=False))

# ============================================================
# 2. DISTRIBUSI SUMBER DATA WISATA
# ============================================================
print("\n" + "=" * 70)
print("DISTRIBUSI SUMBER_DATA WISATA (top 20):")
print("=" * 70)
sumber_count = df['Sumber_Data'].value_counts().head(20)
print(sumber_count.to_string())
print(f"\nTotal nilai unik Sumber_Data: {df['Sumber_Data'].nunique()}")

# ============================================================
# 3. KLASIFIKASI SUMBER UNTUK TABEL 4.14
# ============================================================
print("\n" + "=" * 70)
print("KLASIFIKASI KATEGORI SUMBER WISATA:")
print("=" * 70)

def klasifikasi(sumber):
    s = str(sumber).lower()
    if 'snippet' in s or 'google' in s:
        return 'Google Search Snippet'
    if 'traveloka' in s:
        return 'Traveloka'
    if 'tiket.com' in s:
        return 'Tiket.com'
    if 'travelspromo' in s:
        return 'Travelspromo'
    if 'instagram' in s or 'facebook' in s or 'tiktok' in s:
        return 'Media Sosial'
    if 'kompas' in s or 'tribun' in s or 'detik' in s or 'tempo' in s or 'liputan6' in s or 'okezone' in s or 'cnnindonesia' in s:
        return 'Portal Berita'
    return 'Travel blog / web wisata lainnya'

df['Kategori_Sumber'] = df['Sumber_Data'].apply(klasifikasi)
kategori_count = df['Kategori_Sumber'].value_counts()
total = len(df)
print(f"{'Kategori':<40} | {'Jumlah':>7} | {'Persentase':>10}")
print("-" * 65)
for kat, n in kategori_count.items():
    print(f"{kat:<40} | {n:>7} | {n/total*100:>9.1f}%")
print("-" * 65)
print(f"{'TOTAL':<40} | {total:>7} | {'100.0':>9}%")

# ============================================================
# 4. STATISTIK HOTEL DAN KULINER (untuk konsistensi)
# ============================================================
print("\n" + "=" * 70)
print("STATISTIK HARGA HOTEL DAN KULINER (untuk verifikasi):")
print("=" * 70)
for nama, file in [("Hotel", "hotel_clean.xlsx"), ("Kuliner", "tempat_makan_clean.xlsx")]:
    try:
        d = pd.read_excel(file)
        h = d['Estimasi_Harga']
        print(f"\n{nama} (N={len(d)}):")
        print(f"  Min:    Rp {int(h.min()):,}")
        print(f"  Median: Rp {int(h.median()):,}")
        print(f"  Mean:   Rp {int(h.mean()):,}")
        print(f"  Max:    Rp {int(h.max()):,}")
        print(f"  Std:    Rp {int(h.std()):,}")
    except Exception as e:
        print(f"{nama}: gagal baca ({e})")