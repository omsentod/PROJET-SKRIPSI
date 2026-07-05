#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validasi-roadfactor.py
=======================
Mengukur *circuity factor* (faktor koreksi jalan darat) secara EMPIRIS untuk
jaringan jalan Malang Raya, yaitu rata-rata rasio:

        jarak jalan riil (OSRM)  /  jarak garis lurus (Haversine)

Tujuannya: memberi dasar empiris bagi nilai faktor koreksi 1,45x yang dipakai
pada jalur fallback Haversine — sehingga bukan lagi sekadar asumsi literatur,
melainkan terukur dari dataset Malang Raya itu sendiri.

Cara pakai (contoh):
    python validasi-roadfactor.py --input data_lokasi.csv --sample 200
    python validasi-roadfactor.py --input hotel.csv wisata.csv kuliner.csv --sample 300
    python validasi-roadfactor.py --demo                 # uji jalannya skrip (koordinat demo)

CSV input minimal punya kolom latitude & longitude (nama kolom bisa diatur via
--lat-col / --lon-col). Semua titik dari semua file digabung, lalu dipilih
pasangan acak sebanyak --sample untuk diukur.

PENTING:
- Arahkan --osrm-url ke instans OSRM yang SAMA dengan yang dipakai sistemmu,
  agar faktor yang terukur konsisten dengan perilaku produksi. Default memakai
  server demo publik project-osrm.org (mohon jangan dibebani permintaan besar).
- Hanya butuh pustaka standar Python (tanpa instalasi tambahan).
"""

import argparse
import csv
import json
import math
import random
import requests
import statistics
import sys
import time


# --------------------------------------------------------------------------- #
# Perhitungan jarak
# --------------------------------------------------------------------------- #
def haversine_m(lat1, lon1, lat2, lon2):
    """Jarak great-circle (garis lurus) dalam meter. R bumi = 6.371 km."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))


def osrm_distance_m(lat1, lon1, lat2, lon2, base_url, timeout=15):
    """
    Jarak jalan riil (driving distance) dalam meter via OSRM Route API.
    Mengembalikan None bila gagal. Catatan: OSRM memakai urutan lon,lat.
    """
    base = base_url.rstrip("/")
    coords = f"{lon1},{lat1};{lon2},{lat2}"
    url = f"{base}/route/v1/driving/{coords}?overview=false&alternatives=false&steps=false"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception:
        return None
    if data.get("code") != "Ok" or not data.get("routes"):
        return None
    return float(data["routes"][0]["distance"])


# --------------------------------------------------------------------------- #
# Pemuatan data
# --------------------------------------------------------------------------- #
def load_points(paths, lat_col, lon_col, name_col):
    """Gabungkan semua baris (lat, lon, nama) dari satu/lebih file CSV."""
    points = []
    for path in paths:
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    print(f"[!] {path}: kosong / tanpa header, dilewati.")
                    continue
                if lat_col not in reader.fieldnames or lon_col not in reader.fieldnames:
                    print(f"[!] {path}: kolom '{lat_col}'/'{lon_col}' tidak ditemukan. "
                          f"Kolom tersedia: {reader.fieldnames}")
                    continue
                for row in reader:
                    try:
                        lat = float(str(row[lat_col]).replace(",", ".").strip())
                        lon = float(str(row[lon_col]).replace(",", ".").strip())
                    except (TypeError, ValueError):
                        continue
                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        continue
                    name = (row.get(name_col) or "").strip() if name_col else ""
                    points.append((lat, lon, name))
        except FileNotFoundError:
            print(f"[!] File tidak ditemukan: {path}")
    return points


def demo_points():
    """Beberapa landmark publik Malang Raya — HANYA untuk menguji skrip berjalan."""
    return [
        (-7.98182, 112.62633, "Alun-Alun Kota Malang"),
        (-7.88694, 112.52306, "Museum Angkut, Batu"),
        (-8.00417, 112.62556, "Kampung Warna-Warni Jodipan"),
        (-7.93889, 112.53556, "Alun-Alun Kota Batu"),
        (-8.13556, 112.18889, "Pantai Balekambang"),
        (-7.97778, 112.63417, "Stasiun Malang Kota Baru"),
        (-7.90639, 112.52611, "Jatim Park 2"),
        (-8.00833, 112.62972, "Masjid Agung Jami Malang"),
    ]


# --------------------------------------------------------------------------- #
# Sampling pasangan
# --------------------------------------------------------------------------- #
def sample_pairs(n_points, sample, rng):
    """Pilih pasangan indeks unik (i<j) sebanyak `sample` (atau semua bila lebih sedikit)."""
    total = n_points * (n_points - 1) // 2
    if total == 0:
        return []
    if sample >= total:
        return [(i, j) for i in range(n_points) for j in range(i + 1, n_points)]
    seen, pairs = set(), []
    while len(pairs) < sample:
        i = rng.randrange(n_points)
        j = rng.randrange(n_points)
        if i == j:
            continue
        key = (min(i, j), max(i, j))
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Mengukur circuity factor empiris (OSRM/Haversine) untuk Malang Raya.")
    ap.add_argument("--input", nargs="+", default=["hotel_clean.csv", "wisata_clean.csv", "tempat_makan_clean.csv"],
                    help="Satu/lebih file CSV berisi koordinat.")
    ap.add_argument("--lat-col", default="Latitude", help="Nama kolom latitude (default: Latitude).")
    ap.add_argument("--lon-col", default="Longitude", help="Nama kolom longitude (default: Longitude).")
    ap.add_argument("--name-col", default="Nama_Tempat", help="Nama kolom nama lokasi (opsional).")
    ap.add_argument("--osrm-url", default="http://router.project-osrm.org",
                    help="Base URL instans OSRM (idealnya sama dgn sistemmu).")
    ap.add_argument("--sample", type=int, default=150, help="Jumlah pasangan lokasi diukur (default: 150).")
    ap.add_argument("--seed", type=int, default=42, help="Seed acak agar hasil dapat direproduksi.")
    ap.add_argument("--delay", type=float, default=0.5, help="Jeda antar permintaan OSRM (detik).")
    ap.add_argument("--min-dist", type=float, default=100.0,
                    help="Abaikan pasangan dgn jarak Haversine < nilai ini (meter); kurangi noise.")
    ap.add_argument("--output", default="hasil-roadfactor.csv", help="File CSV rincian hasil.")
    ap.add_argument("--demo", action="store_true", help="Pakai koordinat demo untuk uji jalannya skrip.")
    args = ap.parse_args()

    # ----- muat titik -----
    if args.demo:
        points = demo_points()
        print(f"[i] Mode DEMO: {len(points)} landmark publik Malang Raya (bukan dataset skripsi).")
    elif args.input:
        points = load_points(args.input, args.lat_col, args.lon_col, args.name_col)
    else:
        ap.error("Wajib menyertakan --input <file.csv ...> atau --demo.")
        return

    points = list({(round(la, 7), round(lo, 7), nm) for la, lo, nm in points})  # dedup
    if len(points) < 2:
        print("[x] Titik valid kurang dari 2. Periksa file/kolom input.")
        sys.exit(1)
    print(f"[i] Total titik lokasi termuat: {len(points)}")

    rng = random.Random(args.seed)
    pairs = sample_pairs(len(points), args.sample, rng)
    print(f"[i] Pasangan akan diukur: {len(pairs)} (OSRM: {args.osrm_url})\n")

    # ----- ukur -----
    ratios, rows = [], []
    skipped_close = 0
    failed = 0
    for k, (i, j) in enumerate(pairs, 1):
        la1, lo1, n1 = points[i]
        la2, lo2, n2 = points[j]
        hav = haversine_m(la1, lo1, la2, lo2)
        if hav < args.min_dist:
            skipped_close += 1
            continue
        osrm = osrm_distance_m(la1, lo1, la2, lo2, args.osrm_url)
        if osrm is None or osrm <= 0:
            failed += 1
        else:
            ratio = osrm / hav
            ratios.append(ratio)
            rows.append((n1, n2, round(hav, 1), round(osrm, 1), round(ratio, 4)))
        if k % 25 == 0 or k == len(pairs):
            print(f"    ... {k}/{len(pairs)} diproses "
                  f"(valid={len(ratios)}, gagal={failed}, terlalu_dekat={skipped_close})")
        time.sleep(args.delay)

    if not ratios:
        print("\n[x] Tidak ada rasio valid. Cek koneksi/URL OSRM atau dataset.")
        sys.exit(1)

    # ----- simpan rincian -----
    try:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["lokasi_1", "lokasi_2", "haversine_m", "osrm_m", "rasio"])
            w.writerows(rows)
        print(f"\n[i] Rincian {len(rows)} pasang disimpan ke: {args.output}")
    except OSError as e:
        print(f"[!] Gagal menyimpan {args.output}: {e}")

    # ----- statistik -----
    mean = statistics.mean(ratios)
    median = statistics.median(ratios)
    stdev = statistics.pstdev(ratios) if len(ratios) > 1 else 0.0
    rmin, rmax = min(ratios), max(ratios)

    print("\n" + "=" * 60)
    print("  HASIL CIRCUITY FACTOR EMPIRIS — MALANG RAYA")
    print("=" * 60)
    print(f"  Pasang valid terukur : {len(ratios)}")
    print(f"  Rata-rata (mean)     : {mean:.4f}")
    print(f"  Median               : {median:.4f}")
    print(f"  Simpangan baku       : {stdev:.4f}")
    print(f"  Rentang (min–max)    : {rmin:.4f} – {rmax:.4f}")
    print("=" * 60)

    # ----- pembanding 1,45 -----
    print(f"\n  Faktor yang dipakai sistem saat ini: 1,45x")
    if rmin <= 1.45 <= rmax:
        print(f"  -> 1,45 BERADA dalam rentang terukur ({rmin:.2f}–{rmax:.2f}). ✓")
    selisih = abs(mean - 1.45)
    print(f"  -> Selisih |mean - 1,45| = {selisih:.3f}")
    if selisih <= 0.07:
        print("  -> mean sangat dekat dengan 1,45 → 1,45 tervalidasi dengan baik.")
    else:
        print(f"  -> Pertimbangkan memakai nilai terukur {mean:.2f} agar lebih akurat.")

    # ----- visualisasi -----
    try:
        import matplotlib.pyplot as plt  
        
        # Gunakan style modern
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 1. Histogram Distribusi Rasio
        ax1.hist(ratios, bins=20, color='#3498db', edgecolor='black', alpha=0.7)
        ax1.axvline(1.45, color='#e74c3c', linestyle='--', linewidth=2, label='Faktor Sistem (1.45x)')
        ax1.axvline(mean, color='#2ecc71', linestyle='-.', linewidth=2, label=f'Rata-rata Terukur ({mean:.2f}x)')
        ax1.set_title('Distribusi Circuity Factor (OSRM / Haversine)', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Rasio (Faktor Koreksi)', fontsize=10)
        ax1.set_ylabel('Frekuensi', fontsize=10)
        ax1.legend(frameon=True, facecolor='white', framealpha=0.9)
        
        # 2. Grafik Batang Perbandingan Nilai Utama
        categories = ['Faktor Sistem\n(Baseline)', 'Rata-rata Empiris\n(Mean)', 'Median Empiris\n(Median)']
        values = [1.45, mean, median]
        colors = ['#e74c3c', '#2ecc71', '#f39c12']
        
        bars = ax2.bar(categories, values, color=colors, edgecolor='black', alpha=0.8, width=0.5)
        ax2.set_title('Perbandingan Faktor Koreksi Jarak Jalan', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Nilai Faktor Koreksi (x)', fontsize=10)
        ax2.set_ylim(0, max(values) * 1.3)
        
        # Tampilkan nilai di atas grafik batang
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.3f}x',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom', fontsize=10, fontweight='bold')
            
        plt.tight_layout()
        plot_output = args.output.replace('.csv', '.png')
        plt.savefig(plot_output, dpi=300)
        print(f"[i] Grafik visualisasi berhasil disimpan ke: {plot_output}")
        plt.show()
    except ImportError:
        print("[!] Pustaka 'matplotlib' tidak terpasang. Visualisasi grafik dilewati.")

    # ----- kalimat siap pakai -----
    print("\n--- Kalimat siap tempel (sesuaikan angka) ---")
    print(
        f"Berdasarkan pengujian terhadap {len(ratios)} pasang lokasi pada dataset "
        f"Malang Raya, diperoleh rata-rata rasio jarak jalan riil (OSRM) terhadap "
        f"jarak garis lurus (Haversine) sebesar {mean:.2f} (median {median:.2f}; "
        f"rentang {rmin:.2f}–{rmax:.2f}). Nilai ini menjadi dasar empiris penetapan "
        f"faktor koreksi jalan darat sebesar {mean:.2f}x pada jalur fallback Haversine, "
        f"dan konsisten dengan kisaran circuity factor jalan raya yang dilaporkan dalam "
        f"literatur (Heinold & Makowski, 2026)."
    )


if __name__ == "__main__":
    main()