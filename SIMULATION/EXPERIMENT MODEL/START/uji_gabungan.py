# -*- coding: utf-8 -*-
"""
uji_gabungan.py — Uji Gabungan Algoritma FCM, Validasi Xie-Beni, & Rekomendasi
============================================================================
File ini menggabungkan seluruh komponen matematika dan alur sistem rekomendasi:
1. Pembersihan & Normalisasi Otomatis Dataset Excel.
2. Algoritma Fuzzy C-Means (FCM) Manual murni berbasis NumPy.
3. Evaluasi & Validasi Klaster menggunakan Xie-Beni Index (XBI).
4. Simulasi pencarian jumlah klaster optimal (c = 2, 3, 4, 5).
5. Sistem Rekomendasi Paket Wisata (Workflow Budget-First) dengan inisialisasi
   Centroid berbasis Anggaran (Skema Rasio Centroid A-E) dan tarif Gojek Malang Raya.

Dijalankan langsung di terminal secara interaktif!
"""

import os
import math
import numpy as np
import pandas as pd

# ==============================================================================
# 1. KONFIGURASI & STRUKTUR TARIF
# ==============================================================================
RATIO_SCHEMES = {
    "A": (0.5, 1.0, 1.5),   # Sangat Lebar (100%)
    "B": (0.6, 1.0, 1.4),   # Moderat (80%) — Pilihan utama skripsi
    "C": (0.7, 1.0, 1.3),   # Sempit (60%)
    "D": (0.5, 1.0, 2.0),   # Ekstrem (150%)
    "E": (0.8, 1.0, 1.2),   # Sangat Sempit (40%)
}

CLUSTER_LABELS = {
    0: "Hemat",
    1: "Balanced",
    2: "Premium",
}

TRANSPORT_RATES = {
    "GoRide": {
        "rate_per_km": 2250,
        "max_persons": 1,
        "description": "Motor GoRide (1 orang)",
    },
    "GoCar_Standard": {
        "rate_per_km": 5150,
        "max_persons": 4,
        "description": "Mobil GoCar Standard (2-4 orang)",
    },
    "GoCar_XL": {
        "rate_per_km": 6000,
        "max_persons": 6,
        "description": "Mobil GoCar XL (5-6 orang)",
    },
}

# ==============================================================================
# 2. ALGORITMA FUZZY C-MEANS (FCM) MANUAL (NUMPY MURNI)
# ==============================================================================
def fuzzy_c_means_manual(data, n_clusters=3, m=2.0, error=1e-5, max_iter=300, init_centroids=None, seed=42):
    """
    Implementasi algoritma Fuzzy C-Means Manual murni menggunakan NumPy.
    
    Persamaan Matematika yang digunakan:
    1. Pemutakhiran Pusat Klaster (Centroid) vj:
       vj = (Σ (u_ji)^m * xi) / (Σ (u_ji)^m)
    2. Perhitungan Jarak Euclidean d_ji^2:
       d_ji^2 = ||xi - vj||^2
    3. Pemutakhiran Matriks Keanggotaan Fuzzy u_ji:
       u_ji = 1 / Σ (d_ji / d_ki)^(2/(m-1))
    """
    n_samples = len(data)
    # Ubah data menjadi 2D (n_samples, n_features)
    if len(data.shape) == 1:
        data = data.reshape(-1, 1)
    
    n_features = data.shape[1]
    
    np.random.seed(seed)
    
    # 1. Inisialisasi Matriks Keanggotaan (U)
    if init_centroids is not None:
        # Inisialisasi berbasis jarak dari centroid awal yang diberikan (Budget-Anchored)
        init_centroids = np.array(init_centroids).reshape(n_clusters, n_features)
        distances = np.zeros((n_clusters, n_samples))
        for j in range(n_clusters):
            distances[j, :] = np.sum((data - init_centroids[j, :])**2, axis=1)
        distances = np.fmax(distances, 1e-10)
        
        # U_ji = 1 / d_ji^2
        temp = 1.0 / distances
        U = temp / np.sum(temp, axis=0, keepdims=True)
    else:
        # Inisialisasi acak dengan Dirichlet distribution agar jumlah total keanggotaan tiap sampel = 1
        U = np.random.dirichlet(np.ones(n_clusters), size=n_samples).T
    
    centers = np.zeros((n_clusters, n_features))
    
    # 2. Loop Iterasi FCM
    for iteration in range(max_iter):
        U_prev = U.copy()
        
        # A. Hitung Centroid Baru
        for j in range(n_clusters):
            numerator = np.sum((U[j, :] ** m)[:, np.newaxis] * data, axis=0)
            denominator = np.sum(U[j, :] ** m)
            centers[j, :] = numerator / np.fmax(denominator, 1e-10)
            
        # B. Hitung Jarak Kuadrat
        dist_sq = np.zeros((n_clusters, n_samples))
        for j in range(n_clusters):
            dist_sq[j, :] = np.sum((data - centers[j, :])**2, axis=1)
            
        dist_sq = np.fmax(dist_sq, 1e-10)
        
        # C. Update Matriks Keanggotaan U
        temp = dist_sq ** (-1.0 / (m - 1.0))
        U = temp / np.fmax(np.sum(temp, axis=0, keepdims=True), 1e-10)
        
        # D. Cek Konvergensi (Kriteria Berhenti: ||U_baru - U_lama|| < epsilon)
        if np.linalg.norm(U - U_prev) < error:
            break
            
    # Dapatkan label klaster dengan nilai keanggotaan tertinggi
    labels = np.argmax(U, axis=0)
    
    return centers, U, labels, iteration + 1

# ==============================================================================
# 3. METRIK VALIDASI XIE-BENI INDEX (XBI)
# ==============================================================================
def calculate_xie_beni(data, centers, U, m=2.0):
    """
    Menghitung Xie-Beni Index (XBI) berdasarkan Persamaan di skripsi:
    - Persamaan (2.7): Total Variansi (Sigma)
      σ = Σ_{j=1}^{c} Σ_{i=1}^{n} (u_ji)^m * ||xi - cj||²
    - Persamaan (2.8): Separasi Centroid Minimum (sep)
      sep = min_{j≠k} ||cj - ck||²
    - Persamaan (2.9): Xie-Beni Index (XB)
      XB = σ / (n × sep)
      
    *Nilai Xie-Beni semakin kecil menunjukkan kualitas klasterisasi yang semakin baik.
    """
    n_samples = len(data)
    n_clusters = len(centers)
    
    if len(data.shape) == 1:
        data = data.reshape(-1, 1)
    if len(centers.shape) == 1:
        centers = centers.reshape(-1, 1)
        
    # 1. Hitung Total Variansi (σ)
    sigma = 0.0
    for j in range(n_clusters):
        d_sq = np.sum((data - centers[j, :])**2, axis=1)
        sigma += np.sum((U[j, :] ** m) * d_sq)
        
    # 2. Hitung Separasi Centroid Minimum (sep)
    sep = float('inf')
    for j in range(n_clusters):
        for k in range(j + 1, n_clusters):
            d_sq = np.sum((centers[j, :] - centers[k, :])**2)
            if d_sq < sep:
                sep = d_sq
                
    # 3. Hitung Xie-Beni Index
    if sep == 0 or n_samples == 0:
        xb = float('inf')
    else:
        xb = sigma / (n_samples * sep)
        
    return xb, sigma, sep

# ==============================================================================
# 4. FORMULA HAVERSINE & TRANSPORTASI (SIMULASI GOJEK)
# ==============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Formula Haversine untuk menghitung jarak garis lurus di permukaan bumi.
    Jarak dikalikan faktor 1.3 sebagai konversi rute jalan darat riil (Road Factor).
    """
    R = 6371.0  # Radius bumi (km)
    
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c * 1.3

def get_transport_info(num_persons, distance_km):
    """
    Memilih armada Gojek berdasarkan jumlah peserta dan menghitung total tarifnya.
    """
    if num_persons <= 1:
        rate = TRANSPORT_RATES["GoRide"]
    elif num_persons <= 4:
        rate = TRANSPORT_RATES["GoCar_Standard"]
    else:
        rate = TRANSPORT_RATES["GoCar_XL"]
        
    total_cost = distance_km * rate["rate_per_km"]
    return round(total_cost), rate["description"]

# ==============================================================================
# 5. DETEKSI & LOAD DATASET
# ==============================================================================
def find_and_load_excel():
    """
    Pencarian adaptif lokasi dataset Excel dalam workspace Anda.
    Jika file Excel tidak ditemukan, sistem otomatis menggenerasi dataset buatan (mock) 
    agar script tetap berjalan tanpa hambatan bagi Anda.
    """
    directories_to_check = [
        os.path.dirname(os.path.abspath(__file__)),
        "./SIMULATION/VALIDASI DATA",
        "./SCRAPING",
        "../Malang-Raya/storage/app/python",
        "./MODEL/CLUSTERING/dbset",
        "."
    ]
    
    files = {
        "wisata": ["wisataV2-htm.xlsx", "wisata.xlsx", "wisata_normalized.xlsx"],
        "hotel": ["hotelV2-htm.xlsx", "hotel.xlsx", "hotel_normalized.xlsx"],
        "kuliner": ["tempat_makanV2-htm.xlsx", "tempat-makan.xlsx", "makan_normalized.xlsx"]
    }
    
    loaded_data = {}
    
    print("\n🔍 Memulai pencarian file dataset...")
    for key, filenames in files.items():
        found = False
        for directory in directories_to_check:
            for filename in filenames:
                path = os.path.join(directory, filename)
                if os.path.exists(path):
                    try:
                        df = pd.read_excel(path)
                        # Validasi kecocokan kolom
                        if "Estimasi_Harga" in df.columns:
                            loaded_data[key] = df
                            print(f"   ✅ Ditemukan {key.upper():8} -> {path} ({len(df)} baris)")
                            found = True
                            break
                    except Exception as e:
                        pass
            if found:
                break
                
        # Generate data dummy berkelas jika tidak ditemukan di sistem user
        if key not in loaded_data:
            print(f"   ⚠️  Dataset {key.upper()} tidak ditemukan. Membuat dataset simulasi cerdas...")
            np.random.seed(42)
            n_dummy = 50
            
            if key == "wisata":
                prices = np.random.choice([10000, 15000, 20000, 35000, 50000, 75000, 100000], size=n_dummy)
                names = [f"Destinasi Alam/Buatan {i+1}" for i in range(n_dummy)]
            elif key == "hotel":
                prices = np.random.choice([150000, 250000, 350000, 500000, 750000, 1200000], size=n_dummy)
                names = [f"Hotel Bintang {np.random.randint(1, 6)} - {i+1}" for i in range(n_dummy)]
            else: # kuliner
                prices = np.random.choice([15000, 25000, 35000, 50000, 85000], size=n_dummy)
                names = [f"Resto/Warung Kuliner {i+1}" for i in range(n_dummy)]
                
            # Koordinat area Malang Raya
            lats = np.random.uniform(-7.98, -7.80, size=n_dummy)
            lons = np.random.uniform(112.55, 112.70, size=n_dummy)
            
            loaded_data[key] = pd.DataFrame({
                "Id_Tempat": range(1, n_dummy + 1),
                "Nama_Tempat": names,
                "Estimasi_Harga": prices,
                "Latitude": lats,
                "Longitude": lons
            })
            
    return loaded_data

# ==============================================================================
# OPSI MENU 1: EKSEKUSI FCM & XIE-BENI INTERAKTIF
# ==============================================================================
def menu_fcm_xie_beni(datasets):
    print("\n" + "="*60)
    print(" 🛠️  PENGUJIAN ALGORITMA FUZZY C-MEANS & XIE-BENI INDEX")
    print("="*60)
    
    # Pilih Dataset
    print("Pilih Kategori Dataset:")
    print(" 1. Tempat Wisata")
    print(" 2. Akomodasi (Hotel)")
    print(" 3. Kuliner (Tempat Makan)")
    cat_choice = input("Masukkan pilihan (1-3): ").strip()
    
    cat_map = {"1": "wisata", "2": "hotel", "3": "kuliner"}
    cat_name = cat_map.get(cat_choice, "wisata")
    df = datasets[cat_name].copy()
    
    # Input Parameter FCM
    try:
        c = int(input("Masukkan jumlah klaster (c, default 3): ") or 3)
        m = float(input("Masukkan fuzzifier (m pembobot, default 2.0): ") or 2.0)
    except ValueError:
        print("❌ Input tidak valid! Menggunakan nilai default.")
        c = 3
        m = 2.0
        
    prices = df["Estimasi_Harga"].values
    
    print(f"\n🔄 Menjalankan FCM Manual pada data {cat_name.upper()}...")
    centers, U, labels, iters = fuzzy_c_means_manual(prices, n_clusters=c, m=m)
    
    # Hitung Xie-Beni Index
    xb, sigma, sep = calculate_xie_beni(prices, centers, U, m=m)
    
    # Urutkan Centroid & Label
    sorted_idx = np.argsort(centers.flatten())
    sorted_centers = centers.flatten()[sorted_idx]
    
    print("\n" + "-"*50)
    print(f"📊  HASIL EVALUASI KLASTER ({cat_name.upper()})")
    print("-"*50)
    print(f"✓ Jumlah Iterasi Konvergen: {iters}")
    print(f"✓ Total Variansi (Sigma)  : {sigma:,.2f}")
    print(f"✓ Separasi Centroid (sep) : {sep:,.2f}")
    print(f"📌 Xie-Beni Index (XBI)   : {xb:.6f}")
    print("-"*50)
    
    print("\nPusat Klaster (Centroid) setelah diurutkan:")
    labels_list = ["Murah/Hemat", "Sedang/Balanced", "Mahal/Premium"] if c == 3 else [f"Cluster {i+1}" for i in range(c)]
    for i in range(c):
        label_text = labels_list[i] if i < len(labels_list) else f"Cluster {i+1}"
        print(f"  • {label_text:18} : Rp {sorted_centers[i]:,.0f}")
        
    # Detail Keanggotaan 5 Data Teratas
    print("\nMatriks Keanggotaan Fuzzy (U) 5 Data Pertama:")
    print("-" * 65)
    header = f"{'Nama Tempat':<25} | {'Harga':<12} | " + " | ".join([f"U_{i+1}" for i in range(c)])
    print(header)
    print("-" * 65)
    for i in range(min(5, len(df))):
        u_vals = " | ".join([f"{U[j, i]:.4f}" for j in range(c)])
        print(f"{df['Nama_Tempat'].iloc[i][:25]:<25} | Rp {df['Estimasi_Harga'].iloc[i]:<9,.0f} | {u_vals}")
    print("-" * 65)

# ==============================================================================
# OPSI MENU 2: PENCARIAN KLASTER OPTIMAL (OPTIMAL c SEARCH)
# ==============================================================================
def menu_optimal_c_search(datasets):
    print("\n" + "="*60)
    print(" 📊 PENCARIAN JUMLAH KLASTER OPTIMAL c = [2, 3, 4, 5]")
    print("="*60)
    
    print("Pilih Kategori Dataset:")
    print(" 1. Tempat Wisata")
    print(" 2. Akomodasi (Hotel)")
    print(" 3. Kuliner (Tempat Makan)")
    cat_choice = input("Masukkan pilihan (1-3): ").strip()
    
    cat_map = {"1": "wisata", "2": "hotel", "3": "kuliner"}
    cat_name = cat_map.get(cat_choice, "wisata")
    df = datasets[cat_name]
    prices = df["Estimasi_Harga"].values
    
    c_range = [2, 3, 4, 5]
    best_c = 3
    min_xb = float('inf')
    results = []
    
    print(f"\n🔄 Memulai simulasi pencarian untuk {cat_name.upper()}...")
    print("-" * 75)
    print(f"{'c':<5} | {'Xie-Beni Index':<18} | {'Total Variansi (σ)':<20} | {'Separasi (sep)':<15}")
    print("-" * 75)
    
    for c in c_range:
        centers, U, _, _ = fuzzy_c_means_manual(prices, n_clusters=c, m=2.0)
        xb, sigma, sep = calculate_xie_beni(prices, centers, U, m=2.0)
        
        results.append((c, xb, sigma, sep))
        print(f"{c:<5} | {xb:<18.6f} | {sigma:<20,.2f} | {sep:<15,.2f}")
        
        if xb < min_xb:
            min_xb = xb
            best_c = c
            
    print("-" * 75)
    print(f"🌟 KLASTER OPTIMAL KATEGORI {cat_name.upper()} ADALAH c = {best_c}")
    print(f"   (Memiliki Nilai Xie-Beni Index terkecil yaitu {min_xb:.6f})")
    print("-" * 75)

# ==============================================================================
# OPSI MENU 3: REKOMENDASI PAKET WISATA (BUDGET-FIRST WORKFLOW)
# ==============================================================================
def menu_recommendation(datasets):
    print("\n" + "="*60)
    print(" 🎯 SISTEM REKOMENDASI PAKET WISATA (BUDGET-FIRST WORKFLOW)")
    print("="*60)
    
    # 1. Terima Input Parameter Rekomendasi
    try:
        budget = float(input("Masukkan Total Budget Anda (Rupiah, contoh 1500000): ") or 1500000)
        persons = int(input("Masukkan Jumlah Peserta (orang, default 2): ") or 2)
        duration = int(input("Masukkan Durasi Liburan (hari, default 2): ") or 2)
        
        print("\nSkema Rasio Centroid Inisialisasi:")
        for code, ratio in RATIO_SCHEMES.items():
            print(f"  [{code}] : Hemat={ratio[0]}x, Balanced={ratio[1]}x, Premium={ratio[2]}x")
        scheme_choice = input("Pilih Skema Rasio Centroid (A-E, default B): ").strip().upper()
        if scheme_choice not in RATIO_SCHEMES:
            scheme_choice = "B"
            
    except ValueError:
        print("❌ Masukan tidak valid! Menggunakan nilai default.")
        budget = 1500000
        persons = 2
        duration = 2
        scheme_choice = "B"
        
    print(f"\n⚡ Alur Kerja Utama Skripsi: Mendistribusikan Budget Rp {budget:,.0f} secara proporsional...")
    
    # 2. Distribusi Budget Sesuai Durasi Hari
    if duration == 1:
        # One Day Trip: Tanpa Akomodasi
        allocations = {
            "akomodasi": 0.0,
            "wisata": budget * (15.0 / 60.0),
            "kuliner": budget * (20.0 / 60.0),
            "transportasi": budget * (25.0 / 60.0),
        }
    else:
        # Menginap (Multi-day Trip)
        allocations = {
            "akomodasi": budget * 0.40,
            "wisata": budget * 0.15,
            "kuliner": budget * 0.20,
            "transportasi": budget * 0.25,
        }
        
    print(f"   • Alokasi Akomodasi   (40%): Rp {allocations['akomodasi']:,.0f}")
    print(f"   • Alokasi Wisata      (15%): Rp {allocations['wisata']:,.0f}")
    print(f"   • Alokasi Kuliner     (20%): Rp {allocations['kuliner']:,.0f}")
    print(f"   • Alokasi Transport   (25%): Rp {allocations['transportasi']:,.0f}")
    
    # 3. Konversi ke Anchor Unit (Harga Satuan)
    num_rooms = math.ceil(persons / 2.0)
    nights = duration - 1
    
    # Anchor Per-Unit untuk input FCM
    hotel_anchor = allocations["akomodasi"] / np.fmax(nights * num_rooms, 1.0)
    wisata_anchor = allocations["wisata"] / persons
    kuliner_anchor = allocations["kuliner"] / (persons * 3 * duration)
    
    # 4. Cari Kandidat Terbaik Menggunakan FCM Budget-Anchored
    ratios = RATIO_SCHEMES[scheme_choice]
    
    # Tampilkan Rincian Pecahan Skema Rasio Centroid
    print(f"\n📊 Rincian Target Anggaran Mikro per Kategori (Skema {scheme_choice}: Hemat={ratios[0]}x, Balanced={ratios[1]}x, Premium={ratios[2]}x):")
    print("-" * 75)
    print(f" 🏨 Kategori Akomodasi (Total Alokasi: Rp {allocations['akomodasi']:,.0f}):")
    print(f"    • Target Hemat    ({ratios[0]}x): Rp {allocations['akomodasi'] * ratios[0]:,.0f}")
    print(f"    • Target Balanced ({ratios[1]}x): Rp {allocations['akomodasi'] * ratios[1]:,.0f}")
    print(f"    • Target Premium  ({ratios[2]}x): Rp {allocations['akomodasi'] * ratios[2]:,.0f}")
    print()
    print(f" 🎯 Kategori Wisata (Total Alokasi: Rp {allocations['wisata']:,.0f}):")
    print(f"    • Target Hemat    ({ratios[0]}x): Rp {allocations['wisata'] * ratios[0]:,.0f}")
    print(f"    • Target Balanced ({ratios[1]}x): Rp {allocations['wisata'] * ratios[1]:,.0f}")
    print(f"    • Target Premium  ({ratios[2]}x): Rp {allocations['wisata'] * ratios[2]:,.0f}")
    print()
    print(f" 🍜 Kategori Kuliner (Total Alokasi: Rp {allocations['kuliner']:,.0f}):")
    print(f"    • Target Hemat    ({ratios[0]}x): Rp {allocations['kuliner'] * ratios[0]:,.0f}")
    print(f"    • Target Balanced ({ratios[1]}x): Rp {allocations['kuliner'] * ratios[1]:,.0f}")
    print(f"    • Target Premium  ({ratios[2]}x): Rp {allocations['kuliner'] * ratios[2]:,.0f}")
    print("-" * 75)
    
    # Wadah penyimpanan kandidat per kategori dan per klaster kelas (0=Hemat, 1=Balanced, 2=Premium)
    candidates = {
        "hotel": {0: [], 1: [], 2: []},
        "wisata": {0: [], 1: [], 2: []},
        "kuliner": {0: [], 1: [], 2: []}
    }
    
    for key in ["hotel", "wisata", "kuliner"]:
        df = datasets[key].copy()
        prices = df["Estimasi_Harga"].values
        
        # Hitung centroid awal berdasarkan rasio skema dan anchor
        cat_anchor = hotel_anchor if key == "hotel" else (wisata_anchor if key == "wisata" else kuliner_anchor)
        init_centers = np.array([cat_anchor * r for r in ratios])
        
        # Jalankan FCM Terpandu Centroid Awal
        centers, U, labels, _ = fuzzy_c_means_manual(
            prices, n_clusters=3, m=2.0, init_centroids=init_centers
        )
        
        df["Cluster"] = labels
        
        # Sorting agar Cluster 0=Hemat, 1=Balanced, 2=Premium
        sorted_indices = np.argsort(centers.flatten())
        
        for i in range(3):
            original_cluster_id = sorted_indices[i]
            items_in_c = df[df["Cluster"] == original_cluster_id].copy()
            
            # Hitung target budget untuk kelas ini
            target_price = cat_anchor * ratios[i]
            
            # Jika klaster kosong, ambil dari data terdekat di seluruh data
            if items_in_c.empty:
                df["distance_to_target"] = (df["Estimasi_Harga"] - target_price).abs()
                best_items = df.nsmallest(15, "distance_to_target")
            else:
                items_in_c["distance_to_target"] = (items_in_c["Estimasi_Harga"] - target_price).abs()
                best_items = items_in_c.nsmallest(15, "distance_to_target")
                
            candidates[key][i] = best_items.to_dict("records")

    print("\n🔄 Memproses pencarian kombinasi rute terdekat dan penyaringan budget...")
    
    package_options = {0: [], 1: [], 2: []}
    
    # Aturan jumlah tayang opsi per kelas sesuai permintaan user
    max_options_to_show = {
        0: 5,   # Hemat: Tampilkan maks 5 opsi
        1: 10,  # Balanced: Tampilkan maks 10 opsi
        2: 3,   # Premium: Tampilkan maks 3 opsi
    }
    
    for i in range(3):
        # Ambil daftar kandidat untuk kelas i
        hotel_list = candidates["hotel"][i]
        wisata_list = candidates["wisata"][i]
        kuliner_list = candidates["kuliner"][i]
        
        valid_combinations = []
        
        for h in hotel_list:
            for w in wisata_list:
                for k in kuliner_list:
                    # A. Hitung Biaya Akomodasi
                    if duration > 1:
                        cost_hotel = h["Estimasi_Harga"] * nights * num_rooms
                    else:
                        cost_hotel = 0
                        
                    # B. Hitung Biaya Wisata
                    cost_wisata = w["Estimasi_Harga"] * persons
                    
                    # C. Hitung Biaya Kuliner (3x makan sehari)
                    cost_kuliner = k["Estimasi_Harga"] * persons * 3 * duration
                    
                    # D. Hitung Jarak Spasial Rute Melingkar (Spatial Routing)
                    if duration == 1:
                        # Rute One Day: Kuliner -> Wisata -> Kuliner
                        d1 = haversine_distance(k["Latitude"], k["Longitude"], w["Latitude"], w["Longitude"])
                        total_dist = d1 * 2
                    else:
                        # Rute Menginap: Hotel -> Wisata -> Kuliner -> Hotel
                        d1 = haversine_distance(h["Latitude"], h["Longitude"], w["Latitude"], w["Longitude"])
                        d2 = haversine_distance(w["Latitude"], w["Longitude"], k["Latitude"], k["Longitude"])
                        d3 = haversine_distance(k["Latitude"], k["Longitude"], h["Latitude"], h["Longitude"])
                        total_dist = d1 + d2 + d3
                        
                    # E. Hitung Tarif Transportasi
                    cost_transport, transport_desc = get_transport_info(persons, total_dist)
                    
                    # F. Total Biaya Akumulatif Paket
                    total_pkg_cost = cost_hotel + cost_wisata + cost_kuliner + cost_transport
                    
                    # G. SENSOR ANGGARAN: Hanya loloskan jika di bawah budget riil!
                    if total_pkg_cost <= budget:
                        valid_combinations.append({
                            "hotel": h,
                            "wisata": w,
                            "kuliner": k,
                            "cost_hotel": cost_hotel,
                            "cost_wisata": cost_wisata,
                            "cost_kuliner": cost_kuliner,
                            "cost_transport": cost_transport,
                            "transport_desc": transport_desc,
                            "total_dist": total_dist,
                            "total_cost": total_pkg_cost,
                            "selisih": budget - total_pkg_cost
                        })
                        
        # H. OPTIMASI SPASIAL & RATING (ADAPTIF): Urutkan kombinasi secara dinamis berdasarkan profil kelas budget pengguna
        def get_val(item, key, default=0.0):
            val = item.get(key, default)
            return default if (pd.isna(val) or val is None) else float(val)

        if i == 0:
            # Kelas Hemat: Urutkan berdasarkan jarak spasial terkecil (sangat sensitif terhadap ongkos transport)
            valid_combinations = sorted(valid_combinations, key=lambda x: x["total_dist"])
        elif i == 1:
            # Kelas Balanced: Urutkan secara hybrid (keseimbangan antara rating tertinggi dan jarak terdekat)
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating") * 10 - get_val(x["kuliner"], "Rating") * 2 + x["total_dist"] / 10.0)
            )
        else:
            # Kelas Premium (Sultan): Urutkan berdasarkan Rating tertinggi & Hotel termewah (mengabaikan kendala jarak)
            # Agar destinasi ikonik kelas dunia yang agak jauh (seperti Bromo) tetap ditayangkan di Opsi 1
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating"), -get_val(x["hotel"], "Estimasi_Harga"), x["total_dist"])
            )
        
        # I. Jika tidak ada kombinasi yang di bawah budget (untuk budget sangat rendah),
        # kita ambil 1 kombinasi termurah sebagai fallback darurat (Over Budget)
        if not valid_combinations:
            min_cost_comb = None
            min_cost = float('inf')
            for h in hotel_list[:5]:
                for w in wisata_list[:5]:
                    for k in kuliner_list[:5]:
                        if duration > 1:
                            cost_hotel = h["Estimasi_Harga"] * nights * num_rooms
                        else:
                            cost_hotel = 0
                        cost_wisata = w["Estimasi_Harga"] * persons
                        cost_kuliner = k["Estimasi_Harga"] * persons * 3 * duration
                        if duration == 1:
                            d1 = haversine_distance(k["Latitude"], k["Longitude"], w["Latitude"], w["Longitude"])
                            total_dist = d1 * 2
                        else:
                            d1 = haversine_distance(h["Latitude"], h["Longitude"], w["Latitude"], w["Longitude"])
                            d2 = haversine_distance(w["Latitude"], w["Longitude"], k["Latitude"], k["Longitude"])
                            d3 = haversine_distance(k["Latitude"], k["Longitude"], h["Latitude"], h["Longitude"])
                            total_dist = d1 + d2 + d3
                        cost_transport, transport_desc = get_transport_info(persons, total_dist)
                        total_pkg_cost = cost_hotel + cost_wisata + cost_kuliner + cost_transport
                        if total_pkg_cost < min_cost:
                            min_cost = total_pkg_cost
                            min_cost_comb = {
                                "hotel": h,
                                "wisata": w,
                                "kuliner": k,
                                "cost_hotel": cost_hotel,
                                "cost_wisata": cost_wisata,
                                "cost_kuliner": cost_kuliner,
                                "cost_transport": cost_transport,
                                "transport_desc": transport_desc,
                                "total_dist": total_dist,
                                "total_cost": total_pkg_cost,
                                "selisih": budget - total_pkg_cost
                            }
            if min_cost_comb:
                valid_combinations.append(min_cost_comb)
                
        # Simpan sejumlah maksimal opsi yang ingin ditampilkan
        package_options[i] = valid_combinations[:max_options_to_show[i]]

    # 5. Bangun Paket Wisata Multi-Opsi & Tampilkan Ke Terminal
    print("\n" + "="*60)
    print(" 📦  HASIL REKOMENDASI PAKET WISATA MULTI-OPSI (SPASIAL OPTIMIZED)")
    print("="*60)
    
    for i in range(3):
        label = CLUSTER_LABELS[i]
        options = package_options[i]
        
        print(f"\n=======================================================")
        print(f" 💼 KELAS PAKET: {label.upper()} (Menyajikan {len(options)} Opsi Terdekat)")
        print(f"=======================================================")
        
        if not options:
            print(" ⚠️  Tidak ada kombinasi rekomendasi yang tersedia untuk kelas ini.")
            continue
            
        for idx, opt in enumerate(options):
            h_item = opt["hotel"]
            w_item = opt["wisata"]
            k_item = opt["kuliner"]
            
            status = "✅ UNDER BUDGET" if opt["total_cost"] <= budget else "⚠️ OVER BUDGET"
            
            if duration > 1:
                hotel_detail = f"{h_item['Nama_Tempat']} (Rp {h_item['Estimasi_Harga']:,.0f}/malam)"
            else:
                hotel_detail = "Tanpa Hotel (One Day Trip)"
                
            print(f"\n 📦 OPSI {idx+1} ({status})")
            print("-" * 55)
            print(f"  🏨 Hotel     : {hotel_detail}")
            if duration > 1:
                print(f"                 Rincian: Rp {h_item['Estimasi_Harga']:,.0f} x {nights} malam x {num_rooms} kamar = Rp {opt['cost_hotel']:,.0f}")
            print(f"  🎯 Wisata    : {w_item['Nama_Tempat']}")
            print(f"                 Rincian: Rp {w_item['Estimasi_Harga']:,.0f} x {persons} orang = Rp {opt['cost_wisata']:,.0f}")
            print(f"  🍜 Kuliner   : {k_item['Nama_Tempat']}")
            print(f"                 Rincian: Rp {k_item['Estimasi_Harga']:,.0f} x {persons} orang x 3 makan x {duration} hari = Rp {opt['cost_kuliner']:,.0f}")
            print(f"  🚗 Transport : Rp {opt['cost_transport']:,.0f}")
            print(f"                 Rincian: Rute {opt['total_dist']:.2f} km menggunakan {opt['transport_desc']}")
            print("-" * 55)
            print(f"  💰 ESTIMASI TOTAL BIAYA PAKET : Rp {opt['total_cost']:,.0f}")
            if opt["selisih"] >= 0:
                print(f"  💵 Sisa Anggaran (Kembalian)  : Rp {opt['selisih']:,.0f}")
            else:
                print(f"  💸 Kelebihan Anggaran (Nominal) : Rp {abs(opt['selisih']):,.0f}")
            print("-" * 55)

    # 6. Ekspor Hasil Rekomendasi ke Excel
    excel_rows = []
    for i in range(3):
        label = CLUSTER_LABELS[i]
        options = package_options[i]
        for idx, opt in enumerate(options):
            h_item = opt["hotel"]
            w_item = opt["wisata"]
            k_item = opt["kuliner"]
            
            excel_rows.append({
                "Kelas Paket": label.upper(),
                "No Opsi": idx + 1,
                "Nama Hotel": h_item["Nama_Tempat"] if duration > 1 else "Tanpa Hotel (One Day Trip)",
                "Harga Hotel (Satuan)": h_item["Estimasi_Harga"] if duration > 1 else 0,
                "Total Biaya Hotel": opt["cost_hotel"],
                "Nama Wisata": w_item["Nama_Tempat"],
                "Harga Wisata (Satuan)": w_item["Estimasi_Harga"],
                "Total Biaya Wisata": opt["cost_wisata"],
                "Nama Kuliner": k_item["Nama_Tempat"],
                "Harga Kuliner (Porsi)": k_item["Estimasi_Harga"],
                "Total Biaya Kuliner": opt["cost_kuliner"],
                "Rute Transport (Jarak km)": round(opt["total_dist"], 2),
                "Armada Transport": opt["transport_desc"],
                "Biaya Transport": opt["cost_transport"],
                "Estimasi Total Biaya": opt["total_cost"],
                "Total Budget Input": budget,
                "Sisa Anggaran": opt["selisih"] if opt["selisih"] >= 0 else 0,
                "Kelebihan Anggaran": abs(opt["selisih"]) if opt["selisih"] < 0 else 0,
                "Status": "UNDER BUDGET" if opt["total_cost"] <= budget else "OVER BUDGET"
            })
            
    if excel_rows:
        try:
            export_df = pd.DataFrame(excel_rows)
            output_filename = "rekomendasi_paket.xlsx"
            export_df.to_excel(output_filename, index=False)
            print(f"\n💾  BERHASIL: Seluruh opsi rekomendasi telah diekspor ke Excel!")
            print(f"   📂 File tersimpan di: {os.path.abspath(output_filename)}")
        except Exception as e:
            print(f"\n❌ Gagal mengekspor hasil ke Excel: {e}")

# ==============================================================================
# MENU UTAMA INTERAKTIF TERMINAL
# ==============================================================================
def main():
    print("="*60)
    print("      SISTEM INTEGRASI MATEMATIKA SKRIPSI MALANG RAYA")
    print("      Fuzzy C-Means + Xie-Beni Index + Rekomendasi")
    print("="*60)
    
    # Memuat dataset
    datasets = find_and_load_excel()
    
    while True:
        print("\nMENU PENGUJIAN ALGORITMA DI TERMINAL:")
        print("="*38)
        print(" 1. Run Algoritma FCM Manual & Hitung Xie-Beni Index")
        print(" 2. Pengujian Nilai c Optimal (2 s/d 5) via Xie-Beni Index")
        print(" 3. Simulasi Workflow Rekomendasi Paket Wisata (Budget-First)")
        print(" 4. Keluar dari Program")
        print("="*38)
        
        choice = input("Pilih nomor menu (1-4): ").strip()
        
        if choice == "1":
            menu_fcm_xie_beni(datasets)
        elif choice == "2":
            menu_optimal_c_search(datasets)
        elif choice == "3":
            menu_recommendation(datasets)
        elif choice == "4":
            print("\n👋 Keluar dari sistem pengujian. Terima kasih dan sukses skripsinya!")
            break
        else:
            print("\n❌ Pilihan menu tidak valid. Silakan pilih kembali (1-4).")

if __name__ == "__main__":
    main()
