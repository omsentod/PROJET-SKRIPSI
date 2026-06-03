

import re
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Tuple

# ==============================================================================
# ⚙️  KONSTANTA — EDIT SESUAI KEBUTUHAN ANDA
# ==============================================================================

# --- Path Direktori ---
BASE_DIR  = "/Users/macbookpro/Documents/GITHUB/PROJET-SKRIPSI/PREPOCESSING"
DATA_DIR  = os.path.join(BASE_DIR, "DATA&HTM-NEW")

# --- File Input (nama file persis, case-sensitive) ---
HOTEL_FILE   = os.path.join(DATA_DIR, "hotelV2-htm.xlsx")
KULINER_FILE = os.path.join(DATA_DIR, "tempat_makanV2-htm.xlsx")
WISATA_FILE  = os.path.join(DATA_DIR, "wisataV2-htm.xlsx")

# --- File Output ---
HOTEL_CLEAN_OUT        = os.path.join(BASE_DIR, "hotel_clean.xlsx")
HOTEL_BUANG_OUT        = os.path.join(BASE_DIR, "hotel_dibuang.xlsx")

KULINER_CLEAN_OUT      = os.path.join(BASE_DIR, "tempat_makan_clean.xlsx")
KULINER_BUANG_OUT      = os.path.join(BASE_DIR, "tempat_makan_dibuang.xlsx")

WISATA_CLEAN_OUT       = os.path.join(BASE_DIR, "wisata_clean.xlsx")
WISATA_BUANG_OUT       = os.path.join(BASE_DIR, "wisata_dibuang.xlsx")

LAPORAN_OUT            = os.path.join(BASE_DIR, "laporan_preprocessing.txt")

# --- Kolom wajib yang harus ada di setiap file ---
KOLOM_WAJIB = ["Nama_Tempat", "Estimasi_Harga", "Sumber_Data", "Link_Sumber",
                "Latitude", "Longitude"]

# =============================================================================
# TAHAP 1 — Kata Kunci Indikator Agen Tur (hanya untuk Wisata)
# Edit daftar ini kalau ada pola nama baru yang perlu ditambahkan.
# Pencocokan bersifat case-insensitive dan berbasis substring.
# =============================================================================
KATA_KUNCI_AGEN = [
    "tour",
    "open trip",
    "trip",
    "paket",
    "travel",
    "adventure tour",
    ".id",
    ".com",
    "wisata.com",
    "ekspedisi",
    "organizer",
]

# =============================================================================
# TAHAP 2 — Batas Harga Wajar Tiket Wisata Malang Raya (Rupiah)
# Harga tiket masuk wisata yang wajar umumnya < Rp 300.000.
# Harga di atas ini kemungkinan besar adalah paket tur atau salah-rujuk sumber.
# Ubah nilai ini jika ada pertimbangan akademis yang berbeda.
# =============================================================================
BATAS_HARGA_WISATA_WAJAR = 300_000

# =============================================================================
# TAHAP 4 — Kata Kunci Landmark Tunggal (hanya untuk Wisata)
# Landmark dalam daftar ini secara konsep hanya memiliki SATU titik tiket masuk.
# Jika ada >1 baris yang namanya mengandung keyword yang sama setelah
# filter sebelumnya → pertahankan SATU (kualitas sumber terbaik), sisanya dibuang.
#
# CATATAN: Keyword "bromo" sengaja dibuat spesifik "kawah bromo" agar
# "Bukit Teletubies Bromo" (tempat berbeda) tidak ikut terdeduplikasi.
# Tambahkan keyword lain yang Anda tahu hanya punya satu pintu masuk.
# =============================================================================
LANDMARK_TUNGGAL = [
    "kawah bromo",
    "kawah ijen",
    "ranu kumbolo",
    "semeru",
    "tumpak sewu",
    "coban rondo",
    "coban pelangi",
    "coban sewu",
    "sumber maron",
    "pantai balekambang",
    "pantai goa cina",
    "pantai sendang biru",
    "jatim park 1",
    "jatim park 2",
    "jatim park 3",
    "batu secret zoo",
    "museum angkut",
    "eco green park",
]


# ==============================================================================
# 🛠️  FUNGSI UTILITAS
# ==============================================================================

def baca_excel(path: str, nama_kategori: str) -> Optional[pd.DataFrame]:
    """
    Membaca file Excel dengan penanganan error yang jelas.
    Memeriksa keberadaan file dan ketersediaan kolom wajib.
    """
    if not os.path.exists(path):
        print(f"  ❌ ERROR: File tidak ditemukan → {path}")
        return None

    try:
        df = pd.read_excel(path)
    except Exception as e:
        print(f"  ❌ ERROR: Gagal membaca file {path}\n     Detail: {e}")
        return None

    # Periksa kolom wajib
    kolom_kurang = [k for k in KOLOM_WAJIB if k not in df.columns]
    if kolom_kurang:
        print(f"  ⚠️  PERINGATAN [{nama_kategori}]: Kolom berikut tidak ditemukan: {kolom_kurang}")
        print(f"      Pemrosesan tetap dilanjutkan untuk kolom yang tersedia.")

    return df


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """
    Menghitung jarak garis lurus antara dua koordinat (km) menggunakan formula Haversine.
    Digunakan untuk deduplikasi berbasis kedekatan geografis.
    """
    R = 6371.0
    try:
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    except Exception:
        return float("inf")


def skor_kualitas_sumber(row) -> int:
    """
    Menghitung skor kualitas data suatu baris untuk keperluan tie-breaking deduplikasi.
    Skor lebih tinggi = data lebih terpercaya = diprioritaskan untuk dipertahankan.

    Kriteria:
      +2  → Link_Sumber valid (diawali http — menunjukkan sumber konkret)
      +1  → Estimasi_Harga > 0 (bukan gratis — harga konkret ditemukan)
    """
    skor = 0
    link = str(row.get("Link_Sumber", "")).lower()

    # Link sumber valid
    if link.startswith("http"):
        skor += 2

    # Harga konkret (bukan gratis/0)
    try:
        if float(row.get("Estimasi_Harga", 0)) > 0:
            skor += 1
    except (ValueError, TypeError):
        pass

    return skor


def statistik_harga(df: pd.DataFrame, label: str) -> dict:
    """
    Menghitung statistik deskriptif harga untuk laporan akademis.
    N = total baris (termasuk yang NaN), agar konsisten dengan kolom DATA AWAL.
    Statistik min/median/mean/max/std dihitung hanya dari nilai yang valid (non-NaN).
    """
    if df.empty or "Estimasi_Harga" not in df.columns:
        return {"label": label, "n": 0, "min": "-", "median": "-", "mean": "-", "max": "-", "std": "-"}

    harga = pd.to_numeric(df["Estimasi_Harga"], errors="coerce").dropna()
    return {
        "label":  label,
        "n":      len(df),       # Total baris (inkl. NaN) — konsisten dengan DATA AWAL
        "min":    int(harga.min())    if len(harga) else "-",
        "median": int(harga.median()) if len(harga) else "-",
        "mean":   int(harga.mean())   if len(harga) else "-",
        "max":    int(harga.max())    if len(harga) else "-",
        "std":    int(harga.std())    if len(harga) else "-",
    }


# ==============================================================================
# 📌 TAHAP 1 — Filter Entitas Non-Destinasi / Agen Tur (khusus Wisata)
# ==============================================================================

def tahap1_filter_agen(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Memisahkan baris yang Nama_Tempat-nya mengandung kata kunci indikator agen tur.
    
    Logika pencocokan dua mode:
    1. Keyword mengandung TITIK (.) atau SPASI → SUBSTRING match
       Contoh: ".id", ".com", "open trip", "adventure tour"
    
    2. Keyword KATA TUNGGAL tanpa titik/spasi → WORD BOUNDARY match (regex \\b...\\b)
       Contoh: "tour", "trip", "paket", "travel", "ekspedisi", "organizer"
       Mencegah false positive: "Tour" tidak match dalam "Tourism" atau "Tourist".
    
    Return:
        df_bersih  → baris yang lolos (bukan agen tur)
        df_buang   → baris yang dikeluarkan + kolom Alasan_Dibuang
    """
    if "Nama_Tempat" not in df.columns:
        print("  ⚠️  Kolom Nama_Tempat tidak ditemukan, Tahap 1 dilewati.")
        return df.copy(), pd.DataFrame()
    
    def _cek_nama_agen(nama: str) -> bool:
        """Helper internal: cek apakah nama mengandung indikator agen tur."""
        for kw in KATA_KUNCI_AGEN:
            if "." in kw or " " in kw:
                # Mode SUBSTRING untuk keyword multi-kata atau berdomain
                if kw in nama:
                    return True
            else:
                # Mode WORD BOUNDARY untuk keyword kata tunggal
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, nama):
                    return True
        return False
    
    nama_lower = df["Nama_Tempat"].astype(str).str.lower()
    mask_agen = nama_lower.apply(_cek_nama_agen)
    
    df_buang = df[mask_agen].copy()
    df_buang["Alasan_Dibuang"] = "Entitas non-destinasi (indikasi agen tur)"
    df_bersih = df[~mask_agen].copy()
    
    print(f"  ✅ Tahap 1 selesai: {len(df_buang)} baris dikeluarkan sebagai agen tur.")
    return df_bersih, df_buang
    
# ==============================================================================
# 📌 TAHAP 2 — Filter Harga Anomali (khusus Wisata)
# ==============================================================================

def tahap2_filter_harga_anomali(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Memisahkan baris dengan Estimasi_Harga > BATAS_HARGA_WISATA_WAJAR.
    Batas ini menangkap harga paket tur atau salah-rujuk sumber dari daerah lain.

    Return:
        df_bersih  → baris dengan harga dalam batas wajar
        df_buang   → baris dengan harga anomali + Alasan_Dibuang
    """
    if "Estimasi_Harga" not in df.columns:
        print("  ⚠️  Kolom Estimasi_Harga tidak ditemukan, Tahap 2 dilewati.")
        return df.copy(), pd.DataFrame()

    harga_num = pd.to_numeric(df["Estimasi_Harga"], errors="coerce")
    mask_anomali = harga_num > BATAS_HARGA_WISATA_WAJAR

    df_buang = df[mask_anomali].copy()
    df_buang["Alasan_Dibuang"] = (
        f"Harga melebihi batas wajar tiket wisata Rp {BATAS_HARGA_WISATA_WAJAR:,} "
        "(kemungkinan salah-rujuk atau harga paket tur)"
    )

    df_bersih = df[~mask_anomali].copy()

    print(f"  ✅ Tahap 2 selesai: {len(df_buang)} baris harga anomali dikeluarkan.")
    return df_bersih, df_buang


# ==============================================================================
# 📌 TAHAP 3 — Filter Missing Value / Harga Tidak Valid (semua kategori)
# ==============================================================================

def tahap3_filter_missing(df: pd.DataFrame, izin_gratis: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Memisahkan baris dengan Estimasi_Harga yang tidak valid:
      - NaN / kosong
      - Nilai 0 atau negatif (kecuali izin_gratis=True untuk wisata gratis)

    Parameter:
        izin_gratis → Jika True (wisata), harga 0 DIIZINKAN (wisata gratis masih valid).
                      Jika False (hotel/kuliner), harga 0 dianggap tidak valid.

    Return:
        df_bersih, df_buang
    """
    if "Estimasi_Harga" not in df.columns:
        print("  ⚠️  Kolom Estimasi_Harga tidak ditemukan, Tahap 3 dilewati.")
        return df.copy(), pd.DataFrame()

    harga_num = pd.to_numeric(df["Estimasi_Harga"], errors="coerce")

    if izin_gratis:
        # Wisata: boleh gratis (0), tapi NaN atau negatif tidak valid
        mask_invalid = harga_num.isna() | (harga_num < 0)
    else:
        # Hotel/Kuliner: harus > 0
        mask_invalid = harga_num.isna() | (harga_num <= 0)

    df_buang = df[mask_invalid].copy()
    df_buang["Alasan_Dibuang"] = "Missing value / harga tidak valid (NaN, kosong, atau ≤ 0)"

    df_bersih = df[~mask_invalid].copy()
    # Pastikan kolom Estimasi_Harga bertipe numerik di output bersih
    df_bersih = df_bersih.copy()
    df_bersih["Estimasi_Harga"] = pd.to_numeric(df_bersih["Estimasi_Harga"], errors="coerce")

    print(f"  ✅ Tahap 3 selesai: {len(df_buang)} baris missing/harga tidak valid dikeluarkan.")
    return df_bersih, df_buang


# ==============================================================================
# 📌 TAHAP 4 — Deduplikasi Landmark Tunggal (khusus Wisata)
# ==============================================================================

def tahap4_dedup_landmark(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Mendeteksi dan menangani duplikasi untuk landmark yang secara konsep hanya
    memiliki SATU tiket masuk (didefinisikan di LANDMARK_TUNGGAL).

    Algoritma:
      1. Untuk setiap keyword landmark, cari baris yang Nama_Tempat-nya mengandung
         keyword tersebut (case-insensitive).
      2. Jika ditemukan lebih dari 1 baris → hitung skor kualitas sumber tiap baris.
      3. Pertahankan baris dengan skor tertinggi (tie-break: Estimasi_Harga terendah).
      4. Sisa baris → dipindahkan ke df_buang dengan keterangan landmark mana.

    Setelah filter landmark, jalankan juga dedup nama persis (normalisasi nama):
      - Nama yang sama persis (setelah lowercase + strip) → pertahankan satu terbaik.

    Return:
        df_bersih, df_buang_dedup
    """
    df_work    = df.copy().reset_index(drop=True)
    buang_idxs = {}  # {index_baris: alasan}

    nama_lower = df_work["Nama_Tempat"].astype(str).str.lower().str.strip()

    # --- 5A. Deduplikasi berbasis LANDMARK_TUNGGAL ---
    for keyword in LANDMARK_TUNGGAL:
        mask_kw = nama_lower.str.contains(keyword, regex=False, na=False)
        idx_cocok = df_work.index[mask_kw & ~df_work.index.isin(buang_idxs)].tolist()

        if len(idx_cocok) <= 1:
            continue  # Tidak ada duplikat untuk landmark ini

        # Hitung skor kualitas tiap baris yang cocok
        subset = df_work.loc[idx_cocok].copy()
        subset["_skor"]  = subset.apply(skor_kualitas_sumber, axis=1)
        subset["_harga"] = pd.to_numeric(subset["Estimasi_Harga"], errors="coerce").fillna(float("inf"))

        # Pilih yang terbaik: skor tertinggi, tie-break harga terendah
        subset_sorted = subset.sort_values(["_skor", "_harga"], ascending=[False, True])
        idx_pertahankan = subset_sorted.index[0]

        for idx in idx_cocok:
            if idx != idx_pertahankan:
                nama_pertahankan = df_work.at[idx_pertahankan, "Nama_Tempat"]
                buang_idxs[idx] = (
                    f"Duplikasi landmark '{keyword}' — entitas representatif dipertahankan: "
                    f"'{nama_pertahankan}' (skor kualitas sumber lebih tinggi)"
                )

    # --- 5B. Deduplikasi nama persis (normalisasi sederhana) ---
    # Kelompokkan berdasarkan nama yang sudah dibersihkan
    df_work["_nama_norm"] = nama_lower.str.replace(r"\s+", " ", regex=True).str.strip()
    for nama_norm, grup in df_work.groupby("_nama_norm"):
        idx_grup = [i for i in grup.index if i not in buang_idxs]
        if len(idx_grup) <= 1:
            continue

        subset = df_work.loc[idx_grup].copy()
        subset["_skor"]  = subset.apply(skor_kualitas_sumber, axis=1)
        subset["_harga"] = pd.to_numeric(subset["Estimasi_Harga"], errors="coerce").fillna(float("inf"))

        subset_sorted    = subset.sort_values(["_skor", "_harga"], ascending=[False, True])
        idx_pertahankan  = subset_sorted.index[0]

        for idx in idx_grup:
            if idx != idx_pertahankan:
                buang_idxs[idx] = (
                    f"Duplikasi nama persis '{df_work.at[idx, 'Nama_Tempat']}' — "
                    f"satu entri representatif dipertahankan"
                )

    # Bersihkan kolom bantu
    df_work.drop(columns=["_nama_norm"], errors="ignore", inplace=True)

    # Pisahkan berdasarkan indeks
    df_buang_dedup = df_work.loc[list(buang_idxs.keys())].copy()
    df_buang_dedup["Alasan_Dibuang"] = [buang_idxs[i] for i in df_buang_dedup.index]
    df_bersih = df_work.loc[~df_work.index.isin(buang_idxs)].copy()

    n_dedup = len(buang_idxs)
    n_lm    = sum(1 for v in buang_idxs.values() if "Duplikasi landmark" in v)
    n_nm    = sum(1 for v in buang_idxs.values() if "Duplikasi nama persis" in v)
    print(f"  ✅ Tahap 4 selesai: {n_dedup} baris deduplikasi "
          f"({n_lm} duplikasi landmark, {n_nm} duplikasi nama persis).")

    return df_bersih.reset_index(drop=True), df_buang_dedup.reset_index(drop=True)


# ==============================================================================
# 🏗️  PROSES UTAMA PER KATEGORI
# ==============================================================================

def proses_wisata(df_raw: pd.DataFrame) -> dict:
    """
    Menjalankan 5 tahap filter untuk data Wisata.
    Mengembalikan dict berisi semua dataframe hasil dan ringkasan statistik.
    """
    print("\n" + "─" * 60)
    print("  📍 MEMPROSES WISATA (4 Tahap)")
    print("─" * 60)

    stat_sebelum = statistik_harga(df_raw, "Wisata SEBELUM")
    semua_buang  = []

    # Tahap 1: Filter agen tur
    df1, buang1 = tahap1_filter_agen(df_raw)
    semua_buang.append(buang1)

    # Tahap 2: Filter harga anomali
    df2, buang2 = tahap2_filter_harga_anomali(df1)
    semua_buang.append(buang2)

    # Tahap 3: Filter missing value (wisata boleh gratis → izin_gratis=True)
    df3, buang3 = tahap3_filter_missing(df2, izin_gratis=True)
    semua_buang.append(buang3)

    # Tahap 4: Deduplikasi landmark
    df4, buang4 = tahap4_dedup_landmark(df3)
    semua_buang.append(buang4)

    stat_sesudah = statistik_harga(df4, "Wisata SESUDAH")

    # Gabungkan semua dibuang
    df_dibuang_gabung = pd.concat(
        [b for b in semua_buang if not b.empty], ignore_index=True
    )

    # Ringkasan per alasan buang
    alasan_counts = {}
    if not df_dibuang_gabung.empty:
        for alasan in df_dibuang_gabung["Alasan_Dibuang"]:
            # Ambil kunci alasan singkat (sebelum tanda ':' pertama jika ada)
            kunci = alasan.split("—")[0].strip() if "—" in alasan else alasan[:80]
            alasan_counts[kunci] = alasan_counts.get(kunci, 0) + 1

    return {
        "kategori":       "Wisata",
        "n_awal":         len(df_raw),
        "n_buang":        len(df_dibuang_gabung),
        "n_bersih":       len(df4),
        "alasan_counts":  alasan_counts,
        "stat_sebelum":   stat_sebelum,
        "stat_sesudah":   stat_sesudah,
        "df_bersih":      df4,
        "df_dibuang":     df_dibuang_gabung,
        # Rincian per tahap untuk laporan
        "buang_t1":       len(buang1),
        "buang_t2":       len(buang2),
        "buang_t3":       len(buang3),
        "buang_t4":       len(buang4),
    }


def proses_hotel_kuliner(df_raw: pd.DataFrame, nama: str) -> dict:
    """
    Menjalankan Tahap 3 saja untuk Hotel dan Kuliner (data relatif bersih).
    Hotel/Kuliner tidak menerapkan filter agen, filter harga anomali, atau dedup landmark.
    """
    print("\n" + "─" * 60)
    print(f"  📍 MEMPROSES {nama.upper()} (Tahap 3: Missing Value)")
    print("─" * 60)

    stat_sebelum = statistik_harga(df_raw, f"{nama} SEBELUM")

    # Tahap 3 saja — Hotel/Kuliner harga harus > 0 (izin_gratis=False)
    df_bersih, df_dibuang = tahap3_filter_missing(df_raw, izin_gratis=False)

    stat_sesudah = statistik_harga(df_bersih, f"{nama} SESUDAH")

    alasan_counts = {}
    if not df_dibuang.empty:
        for alasan in df_dibuang["Alasan_Dibuang"]:
            alasan_counts[alasan] = alasan_counts.get(alasan, 0) + 1

    return {
        "kategori":       nama,
        "n_awal":         len(df_raw),
        "n_buang":        len(df_dibuang),
        "n_bersih":       len(df_bersih),
        "alasan_counts":  alasan_counts,
        "stat_sebelum":   stat_sebelum,
        "stat_sesudah":   stat_sesudah,
        "df_bersih":      df_bersih,
        "df_dibuang":     df_dibuang,
    }


# ==============================================================================
# 📄 LAPORAN RINGKASAN
# ==============================================================================

def format_rupiah(val) -> str:
    """Memformat angka ke format Rupiah, atau '-' jika bukan angka."""
    try:
        return f"Rp {int(val):,}"
    except (ValueError, TypeError):
        return str(val)


def cetak_dan_simpan_laporan(hasil_semua: List[dict]) -> None:
    """
    Mencetak laporan ringkasan ke console dan menyimpannya ke laporan_preprocessing.txt.
    Mencakup:
      - Tabel ringkasan jumlah data per kategori
      - Rincian alasan pembuangan per kategori
      - Statistik harga (sebelum vs sesudah) untuk data Wisata
    """
    baris_laporan = []

    def tulis(teks=""):
        print(teks)
        baris_laporan.append(teks)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tulis("=" * 78)
    tulis("  LAPORAN RINGKASAN PREPROCESSING DATA — SKRIPSI SISTEM REKOMENDASI WISATA")
    tulis(f"  Dijalankan pada: {ts}")
    tulis("=" * 78)

    # --- Tabel Ringkasan Utama ---
    tulis(f"\n{'KATEGORI':<14} | {'DATA AWAL':>9} | {'DIBUANG':>8} | {'BERSIH':>8}")
    tulis("-" * 46)
    total_awal = total_buang = total_bersih = 0
    for h in hasil_semua:
        tulis(
            f"{h['kategori']:<14} | {h['n_awal']:>9} | {h['n_buang']:>8} | {h['n_bersih']:>8}"
        )
        total_awal   += h["n_awal"]
        total_buang  += h["n_buang"]
        total_bersih += h["n_bersih"]
    tulis("-" * 46)
    tulis(f"{'TOTAL':<14} | {total_awal:>9} | {total_buang:>8} | {total_bersih:>8}")

    # --- Rincian Alasan Pembuangan per Kategori ---
    tulis("\n" + "=" * 78)
    tulis("  RINCIAN ALASAN PEMBUANGAN PER KATEGORI")
    tulis("=" * 78)
    for h in hasil_semua:
        tulis(f"\n[{h['kategori'].upper()}]")
        if not h["alasan_counts"]:
            tulis("  (Tidak ada baris yang dibuang)")
        else:
            for alasan, jumlah in h["alasan_counts"].items():
                tulis(f"  • {jumlah:>4} baris → {alasan[:70]}")

        # Rincian per tahap untuk wisata
        if h["kategori"] == "Wisata":
            tulis(f"\n  Rincian per Tahap (Wisata):")
            tulis(f"    Tahap 1 - Filter agen tur      : {h.get('buang_t1', 0):>4} baris")
            tulis(f"    Tahap 2 - Harga anomali         : {h.get('buang_t2', 0):>4} baris")
            tulis(f"    Tahap 3 - Missing/harga invalid : {h.get('buang_t3', 0):>4} baris")
            tulis(f"    Tahap 4 - Deduplikasi landmark  : {h.get('buang_t4', 0):>4} baris")

    # --- Statistik Harga Wisata (Sebelum vs Sesudah) ---
    tulis("\n" + "=" * 78)
    tulis("  STATISTIK HARGA WISATA — SEBELUM vs SESUDAH PREPROCESSING")
    tulis("  (Menunjukkan dampak pembersihan terhadap distribusi harga klasterisasi)")
    tulis("=" * 78)

    wisata_hasil = next((h for h in hasil_semua if h["kategori"] == "Wisata"), None)
    if wisata_hasil:
        sb = wisata_hasil["stat_sebelum"]
        ss = wisata_hasil["stat_sesudah"]
        tulis(f"{'METRIK':<12} | {'SEBELUM':>20} | {'SESUDAH':>20}")
        tulis("-" * 58)
        for key, label in [("n", "N data"), ("min", "Min"), ("median", "Median"),
                            ("mean", "Mean"), ("max", "Max"), ("std", "Std Dev")]:
            tulis(
                f"{label:<12} | {format_rupiah(sb[key]) if key != 'n' else sb[key]:>20} | "
                f"{format_rupiah(ss[key]) if key != 'n' else ss[key]:>20}"
            )

    tulis("\n" + "=" * 78)
    tulis("  FILE OUTPUT YANG DIHASILKAN")
    tulis("=" * 78)
    output_files = [
        ("hotel_clean.xlsx",           "Data hotel bersih → input FCM"),
        ("hotel_dibuang.xlsx",         "Data hotel dibuang + Alasan_Dibuang"),
        ("tempat_makan_clean.xlsx",    "Data kuliner bersih → input FCM"),
        ("tempat_makan_dibuang.xlsx",  "Data kuliner dibuang + Alasan_Dibuang"),
        ("wisata_clean.xlsx",          "Data wisata bersih → input FCM"),
        ("wisata_dibuang.xlsx",        "Data wisata dibuang + Alasan_Dibuang"),
        ("laporan_preprocessing.txt",  "Laporan ini"),
    ]
    for nama_file, keterangan in output_files:
        tulis(f"  📄 {nama_file:<35} — {keterangan}")

    tulis("\n" + "=" * 78 + "\n")

    # Simpan ke file teks
    with open(LAPORAN_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(baris_laporan))
    print(f"\n  💾 Laporan tersimpan di: {LAPORAN_OUT}")


# ==============================================================================
# 🚀 FUNGSI UTAMA
# ==============================================================================

def main():
    print("\n" + "=" * 78)
    print("  🚀 MEMULAI PREPROCESSING DATASET SKRIPSI")
    print("  Tujuan: Data bersih untuk input Fuzzy C-Means (variabel: Estimasi_Harga)")
    print("=" * 78)

    hasil_semua = []

    # ── HOTEL ──────────────────────────────────────────────────────────────────
    df_hotel_raw = baca_excel(HOTEL_FILE, "Hotel")
    if df_hotel_raw is not None:
        hasil_hotel = proses_hotel_kuliner(df_hotel_raw, "Hotel")
        hasil_semua.append(hasil_hotel)

        hasil_hotel["df_bersih"].to_excel(HOTEL_CLEAN_OUT, index=False)
        print(f"  💾 hotel_clean.xlsx tersimpan ({len(hasil_hotel['df_bersih'])} baris)")

        if not hasil_hotel["df_dibuang"].empty:
            hasil_hotel["df_dibuang"].to_excel(HOTEL_BUANG_OUT, index=False)
            print(f"  💾 hotel_dibuang.xlsx tersimpan ({len(hasil_hotel['df_dibuang'])} baris)")

    # ── KULINER ────────────────────────────────────────────────────────────────
    df_kuliner_raw = baca_excel(KULINER_FILE, "Kuliner")
    if df_kuliner_raw is not None:
        hasil_kuliner = proses_hotel_kuliner(df_kuliner_raw, "Kuliner")
        hasil_semua.append(hasil_kuliner)

        hasil_kuliner["df_bersih"].to_excel(KULINER_CLEAN_OUT, index=False)
        print(f"  💾 tempat_makan_clean.xlsx tersimpan ({len(hasil_kuliner['df_bersih'])} baris)")

        if not hasil_kuliner["df_dibuang"].empty:
            hasil_kuliner["df_dibuang"].to_excel(KULINER_BUANG_OUT, index=False)
            print(f"  💾 tempat_makan_dibuang.xlsx tersimpan ({len(hasil_kuliner['df_dibuang'])} baris)")

    # ── WISATA ────────────────────────────────────────────────────────────────
    df_wisata_raw = baca_excel(WISATA_FILE, "Wisata")
    if df_wisata_raw is not None:
        hasil_wisata = proses_wisata(df_wisata_raw)
        hasil_semua.append(hasil_wisata)

        hasil_wisata["df_bersih"].to_excel(WISATA_CLEAN_OUT, index=False)
        print(f"  💾 wisata_clean.xlsx tersimpan ({len(hasil_wisata['df_bersih'])} baris)")

        if not hasil_wisata["df_dibuang"].empty:
            hasil_wisata["df_dibuang"].to_excel(WISATA_BUANG_OUT, index=False)
            print(f"  💾 wisata_dibuang.xlsx tersimpan ({len(hasil_wisata['df_dibuang'])} baris)")


    # ── LAPORAN ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("  📊 LAPORAN RINGKASAN PREPROCESSING")
    print("=" * 78)
    cetak_dan_simpan_laporan(hasil_semua)

    print("\n  🎉 PREPROCESSING SELESAI. Semua file output tersimpan di:")
    print(f"     {BASE_DIR}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
