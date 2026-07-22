#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
DETEKTOR KATA BAHASA ASING dalam Skripsi PDF
=============================================================================
Menggunakan kamus bahasa Inggris NLTK (236.000+ kata) sebagai sumber deteksi
sungguhan — bukan daftar manual terbatas.

Alur kerja:
  1. Ekstrak teks PDF per halaman (PyMuPDF)
  2. Tokenisasi setiap kata
  3. Cek apakah kata ada di kamus Inggris NLTK → tandai sebagai asing
  4. Filter kata-kata Indonesia umum agar tidak false positive
  5. Beri padanan / keterangan dari KAMUS_PADANAN jika tersedia
  6. Export ke CSV

Dependensi:
    pip install pymupdf pandas nltk

Cara menjalankan:
    python3 deteksi_eyd.py
=============================================================================
"""

import re
import sys
import unicodedata
from pathlib import Path
from collections import Counter

# ─── Pengecekan dependensi ────────────────────────────────────────────────────
try:
    import fitz
except ImportError:
    print("[ERROR] pip install pymupdf"); sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[ERROR] pip install pandas"); sys.exit(1)

try:
    import nltk
    from nltk.corpus import words as nltk_words_corpus
except ImportError:
    print("[ERROR] pip install nltk"); sys.exit(1)

# ─── Download corpus NLTK jika belum ada ──────────────────────────────────────
for corpus in ("words", "stopwords"):
    try:
        nltk.data.find(f"corpora/{corpus}")
    except LookupError:
        print(f"[INFO] Mengunduh NLTK corpus '{corpus}'...")
        nltk.download(corpus, quiet=True)

from nltk.corpus import stopwords as nltk_stopwords


# ─── Konfigurasi ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "SKRIPSI NEW OS_compressed.pdf"
OUTPUT_CSV = BASE_DIR / "hasil_deteksi_eyd.csv"

# Panjang minimum kata yang diperiksa (hindari false positive kata pendek)
MIN_PANJANG_KATA = 4


# ═════════════════════════════════════════════════════════════════════════════
# KAMUS PADANAN: kata Inggris → (padanan Indonesia, keterangan)
# Digunakan untuk memberi saran EYD pada kata yang terdeteksi sebagai asing.
# Kata yang tidak ada di sini tetap terdeteksi dengan keterangan default.
# ═════════════════════════════════════════════════════════════════════════════
KAMUS_PADANAN = {
    # TI & Komputer
    "website":        ("situs web",              "Gunakan 'situs web' atau cetak miring"),
    "web":            ("web",                    "Cetak miring jika digunakan sebagai istilah asing"),
    "online":         ("daring",                 "Padanan resmi PUEBI: 'daring'"),
    "offline":        ("luring",                 "Padanan resmi PUEBI: 'luring'"),
    "software":       ("perangkat lunak",         "Padanan resmi PUEBI"),
    "hardware":       ("perangkat keras",         "Padanan resmi PUEBI"),
    "database":       ("basis data",              "Padanan resmi PUEBI"),
    "server":         ("peladen",                "Padanan resmi PUEBI"),
    "network":        ("jaringan",               "Padanan resmi PUEBI"),
    "input":          ("masukan",                "Padanan resmi PUEBI"),
    "output":         ("keluaran",               "Padanan resmi PUEBI"),
    "login":          ("masuk",                  "Padanan resmi PUEBI"),
    "logout":         ("keluar",                 "Padanan resmi PUEBI"),
    "username":       ("nama pengguna",           "Padanan resmi PUEBI"),
    "password":       ("kata sandi",              "Padanan resmi PUEBI"),
    "email":          ("surel",                  "Padanan resmi PUEBI"),
    "download":       ("unduh",                  "Padanan resmi PUEBI"),
    "upload":         ("unggah",                 "Padanan resmi PUEBI"),
    "file":           ("berkas",                 "Padanan resmi PUEBI"),
    "folder":         ("map / direktori",         "Padanan resmi PUEBI"),
    "user":           ("pengguna",               "Padanan resmi PUEBI"),
    "interface":      ("antarmuka",              "Padanan resmi PUEBI"),
    "framework":      ("kerangka kerja",          "Cetak miring atau gunakan 'kerangka kerja'"),
    "feature":        ("fitur",                  "Gunakan 'fitur' (sudah terserap)"),
    "update":         ("pembaruan",              "Padanan resmi PUEBI"),
    "install":        ("instal / pasang",         "Gunakan 'instal' (terserap)"),
    "feedback":       ("umpan balik",             "Padanan resmi PUEBI"),
    "query":          ("kueri",                  "Gunakan 'kueri' (terserap)"),
    "cluster":        ("klaster",                "Gunakan 'klaster' (terserap)"),
    "clustering":     ("pengelompokan",           "Padanan resmi PUEBI"),
    "training":       ("pelatihan",              "Padanan resmi PUEBI"),
    "testing":        ("pengujian",              "Padanan resmi PUEBI"),
    "dataset":        ("kumpulan data",           "Cetak miring atau gunakan 'kumpulan data'"),
    "platform":       ("platform",               "Cetak miring atau sesuaikan konteks"),
    "default":        ("bawaan",                 "Padanan: 'bawaan' atau cetak miring"),
    "error":          ("galat",                  "Padanan resmi PUEBI: 'galat'"),
    "browser":        ("peramban",               "Padanan resmi PUEBI"),
    "coding":         ("pemrograman",            "Padanan resmi PUEBI"),
    "link":           ("tautan",                 "Padanan resmi PUEBI"),
    "search":         ("pencarian",              "Padanan resmi PUEBI"),
    "sorting":        ("pengurutan",             "Padanan resmi PUEBI"),
    "ranking":        ("peringkat",              "Padanan resmi PUEBI"),
    "rating":         ("penilaian",              "Padanan: 'penilaian' atau cetak miring"),
    "mapping":        ("pemetaan",               "Padanan resmi PUEBI"),
    "system":         ("sistem",                 "Gunakan 'sistem' (sudah terserap)"),
    "usability":      ("kegunaan / kemudahan penggunaan", "Padanan: 'kegunaan' atau cetak miring"),
    "scale":          ("skala",                  "Gunakan 'skala' (sudah terserap)"),
    # Nama / istilah teknis
    "fuzzy":          ("kabur / samar",           "Istilah teknis — cetak miring"),
    "means":          ("rata-rata",              "Dalam konteks 'fuzzy c-means': cetak miring"),
    "index":          ("indeks",                 "Gunakan 'indeks' (terserap)"),
    "score":          ("skor",                   "Gunakan 'skor' (terserap)"),
    "weight":         ("bobot",                  "Padanan resmi PUEBI"),
    "threshold":      ("ambang batas",            "Padanan resmi PUEBI"),
    "benchmark":      ("tolok ukur",              "Padanan resmi PUEBI"),
    "prototype":      ("prototipe",              "Gunakan 'prototipe' (terserap)"),
    "workflow":       ("alur kerja",              "Padanan resmi PUEBI"),
    "flowchart":      ("bagan alir",              "Padanan resmi PUEBI"),
    "blackbox":       ("kotak hitam",             "Cetak miring atau gunakan padanan"),
    "testing":        ("pengujian",              "Padanan resmi PUEBI"),
    "case":           ("kasus",                  "Gunakan 'kasus' (sudah terserap)"),
    "pass":           ("lulus / berhasil",        "Dalam konteks pengujian"),
    "best":           ("terbaik",                "Padanan resmi PUEBI"),
    "result":         ("hasil",                  "Padanan resmi PUEBI"),
    "process":        ("proses",                 "Gunakan 'proses' (sudah terserap)"),
    "real":           ("nyata",                  "Padanan: 'nyata'"),
    "detail":         ("rincian",                "Padanan resmi PUEBI"),
    "summary":        ("ringkasan",              "Padanan resmi PUEBI"),
    "objective":      ("tujuan",                 "Padanan resmi PUEBI"),
    "approach":       ("pendekatan",             "Padanan resmi PUEBI"),
    "impact":         ("dampak",                 "Padanan resmi PUEBI"),
    "challenge":      ("tantangan",              "Padanan resmi PUEBI"),
    "background":     ("latar belakang",          "Padanan resmi PUEBI"),
    "implementation": ("implementasi",            "Gunakan 'implementasi' (terserap)"),
    "recommendation": ("rekomendasi",             "Gunakan 'rekomendasi' (terserap)"),
    "scenario":       ("skenario",               "Gunakan 'skenario' (terserap)"),
    "literature":     ("literatur / kepustakaan", "Gunakan 'literatur' (terserap)"),
    "performance":    ("kinerja",                "Padanan resmi PUEBI"),
    "accuracy":       ("akurasi",                "Gunakan 'akurasi' (terserap)"),
    "variable":       ("variabel",               "Gunakan 'variabel' (terserap)"),
    "trend":          ("tren",                   "Gunakan 'tren' (terserap, bukan 'trend')"),
    "gap":            ("kesenjangan",             "Padanan: 'kesenjangan'"),
    "review":         ("tinjauan",               "Gunakan 'tinjauan' dalam konteks akademik"),
    "random":         ("acak",                   "Padanan resmi PUEBI"),
    "sampling":       ("pengambilan sampel",      "Padanan resmi PUEBI"),
    "interview":      ("wawancara",              "Padanan resmi PUEBI"),
    # Pariwisata & Bisnis
    "tour":           ("wisata / tur",            "Cetak miring atau gunakan 'wisata'"),
    "travel":         ("perjalanan",             "Padanan resmi PUEBI"),
    "booking":        ("pemesanan",              "Padanan resmi PUEBI"),
    "budget":         ("anggaran",               "Padanan resmi PUEBI"),
    "market":         ("pasar",                  "Padanan resmi PUEBI"),
    "marketing":      ("pemasaran",              "Padanan resmi PUEBI"),
    "brand":          ("merek",                  "Padanan resmi PUEBI"),
    "startup":        ("perusahaan rintisan",     "Padanan resmi PUEBI"),
    "profit":         ("keuntungan / laba",       "Padanan resmi PUEBI"),
    "stakeholder":    ("pemangku kepentingan",    "Padanan resmi PUEBI"),
}

# ═════════════════════════════════════════════════════════════════════════════
# KATA-KATA INDONESIA UMUM yang sering mirip kata Inggris → DIKECUALIKAN
# (mencegah false positive)
# ═════════════════════════════════════════════════════════════════════════════
KATA_INDONESIA_UMUM = {
    # ── Kata dasar Indonesia yang kebetulan ada di kamus Inggris ──────────────
    "ada", "akan", "atau", "bagi", "bisa", "bila", "agar", "atas",
    "baru", "dari", "dengan", "dalam", "dan", "depan", "dia",
    "dua", "enam", "hari", "hal", "ini", "itu", "jadi", "juga",
    "jika", "kali", "kami", "kamu", "kanan", "karena", "ke", "kita",
    "lain", "lalu", "lama", "lebih", "luar", "maka", "mana", "masa",
    "masih", "milik", "mulai", "nama", "nilai", "oleh", "pada",
    "pagi", "paling", "para", "pasti", "penuh", "per", "pula",
    "sama", "sana", "satu", "saya", "sebagai", "sehingga", "sejak",
    "semua", "sering", "sesuai", "sini", "sisa", "sudah", "sumber",
    "tapi", "tiga", "tidak", "tinggi", "tujuh", "untuk", "yang",
    "yaitu", "serta", "antara", "antar", "jenis", "angka", "besar",
    "kecil", "awal", "akhir", "hasil", "bagian", "tempat", "cara",
    "perlu", "dapat", "harus", "mampu", "akan", "telah", "sedang",
    "yang", "yang", "rata", "nilai", "suatu", "setiap", "sebuah",
    "namun", "tetapi", "meski", "walau", "bahwa", "agar", "supaya",
    "setelah", "sebelum", "ketika", "selama", "saat", "kemudian",
    "namun", "juga", "pun", "hanya", "selain", "saja", "pun",
    "antara", "antar", "serta", "dengan", "tanpa", "hingga", "sampai",
    "karena", "sebab", "akibat", "sehingga", "maka", "agar",
    "batas", "bawah", "tengah", "kiri", "kanan", "depan", "belakang",

    # ── Kata serapan yang SUDAH baku dalam bahasa Indonesia ───────────────────
    "data", "sistem", "metode", "proses", "analisis", "fungsi",
    "faktor", "aspek", "kondisi", "situasi", "solusi", "informasi",
    "teknologi", "komunikasi", "organisasi", "struktur", "program",
    "komputer", "internet", "digital", "media", "aplikasi",
    "nasional", "global", "lokal", "formal", "normal", "natural",
    "final", "optimal", "minimal", "maksimal", "visual", "virtual",
    "teknis", "ekonomi", "sosial", "fisik", "model", "algoritma",
    "parameter", "formula", "matriks", "vektor", "skala", "indeks",
    "skor", "validasi", "implementasi", "rekomendasi", "evaluasi",
    "integrasi", "konfigurasi", "kalkulasi", "komputasi", "simulasi",
    "identifikasi", "klasifikasi", "klasterisasi", "optimasi",
    "akurasi", "presisi", "efisiensi", "efektivitas", "kapasitas",
    "fitur", "modul", "standar", "prosedur", "kriteria", "kategori",
    "klaster", "entitas", "variabel", "atribut", "objek", "subjek",
    "literatur", "hipotesis", "populasi", "sampel", "instrumen",
    "konstruk", "dimensi", "distribusi", "statistik", "probabilitas",
    "regresi", "korelasi", "deviasi", "varians", "frekuensi",
    "persentase", "proporsi", "median", "modus", "rata",
    "abstrak", "deskripsi", "definisi", "konsep", "teori", "praktik",
    "observasi", "eksperimen", "verifikasi", "dokumentasi",
    "presentasi", "komunikasi", "administrasi", "koordinasi",
    "kolaborasi", "partisipasi", "kontribusi", "investasi", "inovasi",
    "transformasi", "adaptasi", "migrasi", "navigasi", "eksplorasi",
    "ekstraksi", "agregasi", "normalisasi", "segmentasi", "filter",
    "iterasi", "konvergensi", "divergensi", "inisialisasi", "dekomposisi",

    # ── Kata-kata yang SUDAH terserap dan lazim dipakai di skripsi TI ─────────
    "website", "framework", "database", "server", "platform",
    "backend", "frontend", "interface", "software", "hardware",
    "network", "internet", "browser", "email", "login", "logout",
    "upload", "download", "update", "install", "backup", "cache",
    "query", "cluster", "clustering", "dataset", "testing",
    "training", "ranking", "rating", "feedback", "default",
    "coding", "scraping", "parsing", "rendering", "routing",
    "debugging", "logging", "monitoring", "deployment", "hosting",

    # ── Kata Inggris yang SANGAT umum dan LAZIM di skripsi tanpa perlu miring ─
    "hotel", "target", "premium", "budget", "first", "centroid",
    "beni", "xie", "index", "score", "case", "pass", "best",
    "black", "box", "white", "grey", "red", "green", "blue",
    "true", "false", "null", "none", "list", "dict", "array",
    "return", "print", "class", "function", "method", "import",

    # ── Nama proper & akronim teknis ──────────────────────────────────────────
    "fuzzy", "fcm", "uml", "erd", "sql", "api", "http", "url",
    "android", "ios", "python", "java", "php", "html", "css",
    "laravel", "mysql", "excel", "google", "viator", "kayak",
    "malang", "jawa", "indonesia", "raya", "usability", "scale",
    "system", "scrum", "agile", "rest", "json", "xml",

    # ── Kata nama/istilah yang terdeteksi tapi bukan kata asing dalam konteks ──
    "serta", "antar", "antara", "belum", "masih", "sudah",
    "harus", "perlu", "dapat", "mampu", "akan", "bisa",
    "pula", "pun", "juga", "lagi", "kini", "dini", "tadi",

    # ── Tambahan false positive yang sering muncul ────────────────────────────
    # Kata Indonesia yang cocok dengan kamus Inggris
    "total", "kota", "orang", "alur", "valid", "label", "lama",
    "tanpa", "maka", "batas", "bawah", "tengah", "atas", "dalam",
    "luar", "depan", "semua", "penuh", "sama", "sana", "sini",
    "sera", "bagi", "bila", "saat", "kali", "masa", "nama",
    "nilai", "mana", "cara", "jenis", "awal", "akhir", "rata",
    "suatu", "setiap", "sebuah", "bagian", "tempat", "hasil",
    "mulai", "milik", "dari", "oleh", "pada", "per", "ada",
    "hari", "hal", "ini", "itu", "jadi", "pagi", "lain",
    "baru", "kita", "kami", "kamu", "saya", "dia",
    # Istilah teknis / nama fitur yang dipakai dalam konteks Indonesia
    "auto", "real", "time", "based", "label", "balanced",
    "destination", "exploration", "flexible", "valid",
    "first", "second", "third", "final", "total", "main",
    "general", "special", "standard", "basic", "core",
    "test", "pass", "fail", "case", "mode", "type", "name",
    "home", "page", "form", "text", "code", "item", "list",
    "line", "step", "path", "node", "edge", "root", "leaf",
    "tree", "graph", "loop", "rate", "cost", "time", "date",
    "size", "rank", "role", "area", "zone", "tier", "user",
}


# ═════════════════════════════════════════════════════════════════════════════
# MEMBANGUN KAMUS INGGRIS dari NLTK
# ═════════════════════════════════════════════════════════════════════════════
print("[INFO] Memuat kamus bahasa Inggris dari NLTK...")
_ENGLISH_WORDS_RAW = set(w.lower() for w in nltk_words_corpus.words())
# Hapus kata-kata sangat pendek yang rawan false positive
_ENGLISH_WORDS = {w for w in _ENGLISH_WORDS_RAW if len(w) >= MIN_PANJANG_KATA}
print(f"[INFO] Kamus Inggris dimuat: {len(_ENGLISH_WORDS):,} kata (min {MIN_PANJANG_KATA} karakter)\n")


# ═════════════════════════════════════════════════════════════════════════════
# FUNGSI UTILITAS
# ═════════════════════════════════════════════════════════════════════════════

def normalisasi_teks(teks):
    teks = unicodedata.normalize("NFKC", teks)
    teks = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", teks)
    return teks


def ekstrak_teks_pdf(path_pdf):
    if not path_pdf.exists():
        print(f"[ERROR] File tidak ditemukan: {path_pdf}")
        sys.exit(1)
    print(f"[INFO] Membuka PDF: {path_pdf.name}")
    doc = fitz.open(str(path_pdf))
    total = doc.page_count
    print(f"[INFO] Total halaman: {total}")
    hasil = []
    for i, hal in enumerate(doc, start=1):
        teks = normalisasi_teks(hal.get_text("text"))
        hasil.append({"halaman": i, "teks": teks})
        if i % 20 == 0:
            print(f"       -> Halaman {i}/{total}...")
    doc.close()
    print(f"[INFO] Ekstraksi selesai.\n")
    return hasil


def tokenisasi_kata(teks):
    """Pecah teks menjadi token kata alfabet saja."""
    return re.findall(r"[a-zA-Z]+", teks)


def ambil_konteks(teks, kata, radius=70):
    """Ambil cuplikan kalimat sekitar kata."""
    bersih = re.sub(r"\s+", " ", teks).strip()
    try:
        idx = bersih.lower().index(kata.lower())
        mulai = max(0, idx - radius)
        akhir = min(len(bersih), idx + len(kata) + radius)
        potongan = bersih[mulai:akhir].strip()
        if mulai > 0:   potongan = "..." + potongan
        if akhir < len(bersih): potongan = potongan + "..."
        return potongan
    except ValueError:
        return "(konteks tidak ditemukan)"


def adalah_kata_inggris(kata):
    """
    Kembalikan True jika kata termasuk kamus Inggris NLTK
    DAN bukan kata Indonesia umum.
    """
    kl = kata.lower()
    if kl in KATA_INDONESIA_UMUM:
        return False
    if len(kl) < MIN_PANJANG_KATA:
        return False
    return kl in _ENGLISH_WORDS


# ═════════════════════════════════════════════════════════════════════════════
# FUNGSI DETEKSI UTAMA
# ═════════════════════════════════════════════════════════════════════════════

def deteksi_kata_asing(halaman_data):
    """
    Deteksi semua kata bahasa Inggris menggunakan kamus NLTK (236k kata).
    Memberi saran padanan dari KAMUS_PADANAN jika tersedia,
    atau keterangan default 'Cetak miring atau ganti padanan Indonesia'.
    """
    temuan = []
    kamus_padanan_lower = {k.lower(): v for k, v in KAMUS_PADANAN.items()}

    for data in halaman_data:
        no_hal = data["halaman"]
        teks = data["teks"]
        kata_kata = tokenisasi_kata(teks)

        seen_pada_halaman = set()

        for kata in kata_kata:
            kl = kata.lower()
            # De-duplikasi per halaman agar tidak berulang terlalu banyak
            if (no_hal, kl) in seen_pada_halaman:
                continue

            if tidak_adalah_kata_inggris(kl):
                continue

            seen_pada_halaman.add((no_hal, kl))

            # Ambil padanan jika ada di KAMUS_PADANAN
            if kl in kamus_padanan_lower:
                padanan, keterangan = kamus_padanan_lower[kl]
                saran = f"{padanan}"
                jenis = f"Kata asing — {keterangan}"
            else:
                saran = "(lihat KBBI / gunakan padanan Indonesia atau cetak miring)"
                jenis = "Kata bahasa Inggris — cetak miring atau ganti padanan"

            temuan.append({
                "Halaman":         no_hal,
                "Kata Asing":      kata,
                "Padanan / Saran": saran,
                "Keterangan":      jenis,
                "Kalimat Konteks": ambil_konteks(teks, kata),
            })

    return temuan


def tidak_adalah_kata_inggris(kl):
    """Wrapper negatif agar kode di atas lebih mudah dibaca."""
    return not adalah_kata_inggris(kl)


def hapus_duplikat_dan_urutkan(temuan):
    seen = set()
    unik = []
    for item in temuan:
        k = (item["Halaman"], item["Kata Asing"].lower())
        if k not in seen:
            seen.add(k)
            unik.append(item)
    return sorted(unik, key=lambda x: (x["Halaman"], x["Kata Asing"].lower()))


def tampilkan_statistik(temuan):
    print("=" * 65)
    print("   STATISTIK DETEKSI KATA BAHASA ASING")
    print("=" * 65)
    print(f"  Total temuan unik   : {len(temuan)}")
    if not temuan:
        print("=" * 65)
        return

    counter_kata = Counter(item["Kata Asing"].lower() for item in temuan)
    print(f"\n  Top 15 Kata Asing Terbanyak:")
    for kata, n in counter_kata.most_common(15):
        print(f"    {kata:<25} -> {n}x")

    counter_hal = Counter(item["Halaman"] for item in temuan)
    print(f"\n  Top 5 Halaman dengan Temuan Terbanyak:")
    for hal, n in counter_hal.most_common(5):
        print(f"    Halaman {hal:<5} -> {n} temuan")

    print("=" * 65)


def simpan_ke_csv(temuan, output_path):
    if not temuan:
        print("[WARN] Tidak ada temuan.")
        return
    kolom = ["Halaman", "Kata Asing", "Padanan / Saran", "Keterangan", "Kalimat Konteks"]
    df = pd.DataFrame(temuan)[kolom]
    df.to_csv(str(output_path), index=False, encoding="utf-8-sig")
    print(f"\n[OK] CSV disimpan: {output_path}")
    print(f"     Total baris  : {len(df)}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "=" * 65)
    print("  DETEKTOR KATA ASING — Skripsi PDF Analyzer (NLTK)")
    print("=" * 65 + "\n")

    halaman_data = ekstrak_teks_pdf(PDF_PATH)

    print("[INFO] Mendeteksi kata bahasa Inggris (kamus NLTK 236k kata)...")
    temuan = deteksi_kata_asing(halaman_data)
    print(f"       Ditemukan {len(temuan)} temuan (sebelum de-duplikasi).")

    temuan = hapus_duplikat_dan_urutkan(temuan)
    print(f"[INFO] Total temuan unik: {len(temuan)}")

    tampilkan_statistik(temuan)
    simpan_ke_csv(temuan, OUTPUT_CSV)

    print("\n[SELESAI] Buka 'hasil_deteksi_eyd.csv' untuk melihat hasil lengkap.\n")


if __name__ == "__main__":
    main()
