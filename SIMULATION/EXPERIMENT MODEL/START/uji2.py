import os
import math
import numpy as np
import pandas as pd

# ==============================================================================
# 1. KONFIGURASI & STRUKTUR TARIF (SELESAI DENGAN RECOMMENDER.PY)
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
# 4. FORMULA HAVERSINE DENGAN FAKTOR JALAN DARAT (ROAD FACTOR 1.3x) & TRANSPORTASI
# ==============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Formula Haversine untuk menghitung jarak garis lurus di permukaan bumi.
    Jarak dikalikan faktor 1.3 sebagai konversi rute jalan darat riil (Road Factor).
    Menyelaraskan estimasi jarak offline dengan Uji_Gabungan dan Recommender.py secara akademis.
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
# 5. DETEKSI & LOAD DATASET SECARA ADAPTIF
# ==============================================================================
def find_and_load_excel():
    """
    Pencarian adaptif lokasi dataset Excel dalam workspace Anda.
    """
    directories_to_check = [
        os.path.dirname(os.path.abspath(__file__)),
        "./SIMULATION/VALIDASI DATA",
        "./SCRAPING",
        "../Malang-Raya/storage/app/python",
        "./storage/app/python",
        "./MODEL/CLUSTERING/dbset",
        "."
    ]
    
    files = {
        "wisata": ["wisata_clean.xlsx"],
        "hotel": ["hotel_clean.xlsx"],
        "kuliner": ["tempat_makan_clean.xlsx"]
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
                        if "Estimasi_Harga" in df.columns:
                            loaded_data[key] = df
                            print(f"   ✅ Ditemukan {key.upper():8} -> {path} ({len(df)} baris)")
                            found = True
                            break
                    except Exception:
                        pass
            if found:
                break
                
        # Generate data dummy jika tidak ditemukan
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
                
            lats = np.random.uniform(-7.98, -7.80, size=n_dummy)
            lons = np.random.uniform(112.55, 112.70, size=n_dummy)
            
            loaded_data[key] = pd.DataFrame({
                "Id_Tempat": range(1, n_dummy + 1),
                "Nama_Tempat": names,
                "Estimasi_Harga": prices,
                "Latitude": lats,
                "Longitude": lons,
                "Rating": np.random.uniform(4.0, 5.0, size=n_dummy)
            })
            
    return loaded_data

# ==============================================================================
# HELPER RUN FCM DENGAN STRUKTUR PUSAT AWAL DAN ANCHOR
# ==============================================================================
def get_cluster_label(idx, c):
    """
    Fungsi untuk menentukan label kategori paket secara akademis & dinamis berdasarkan jumlah klaster c.
    """
    if c == 2:
        labels = ["HEMAT", "PREMIUM"]
    elif c == 3:
        labels = ["HEMAT", "BALANCED", "PREMIUM"]
    elif c == 4:
        labels = ["HEMAT", "BALANCED (LOW)", "BALANCED (HIGH)", "PREMIUM"]
    elif c == 5:
        labels = ["HEMAT", "BALANCED (LOW)", "BALANCED (MEDIUM)", "BALANCED (HIGH)", "PREMIUM"]
    else:
        labels = [f"KLASTER {i+1}" for i in range(c)]
    return labels[idx] if idx < len(labels) else f"KLASTER {idx+1}"

def run_budget_anchored_fcm(data_prices, budget, ratio_scheme="B", n_clusters=3, m=2.0):
    if n_clusters == 3:
        ratios = RATIO_SCHEMES[ratio_scheme]
    elif n_clusters == 2:
        ratios = [0.8, 1.2]
    elif n_clusters == 4:
        ratios = [0.5, 0.8, 1.2, 1.5]
    elif n_clusters == 5:
        ratios = [0.4, 0.7, 1.0, 1.3, 1.6]
    else:
        ratios = np.linspace(0.5, 1.5, n_clusters)
        
    init_centers = np.array([budget * r for r in ratios]).reshape(-1, 1)
    
    centers, U, labels, iters = fuzzy_c_means_manual(
        data_prices, n_clusters=n_clusters, m=m, init_centroids=init_centers
    )
    
    xb, sigma, sep = calculate_xie_beni(data_prices, centers, U, m=m)
    
    sorted_indices = np.argsort(centers.flatten())
    sorted_cntr = centers.flatten()[sorted_indices]
    sorted_u = U[sorted_indices]
    sorted_labels = np.argmax(sorted_u, axis=0)
    
    return {
        "cntr": sorted_cntr,
        "u": sorted_u,
        "labels": sorted_labels,
        "xb": xb
    }

def run_percentile_fcm(data_prices, n_clusters=3, m=2.0):
    q_vals = np.linspace(15, 85, n_clusters)
    init_centers_flat = np.percentile(data_prices, q_vals)
    init_centers = init_centers_flat.reshape(-1, 1)
    
    centers, U, labels, iters = fuzzy_c_means_manual(
        data_prices, n_clusters=n_clusters, m=m, init_centroids=init_centers
    )
    
    xb, sigma, sep = calculate_xie_beni(data_prices, centers, U, m=m)
    
    sorted_indices = np.argsort(centers.flatten())
    sorted_cntr = centers.flatten()[sorted_indices]
    sorted_u = U[sorted_indices]
    sorted_labels = np.argmax(sorted_u, axis=0)
    
    return {
        "cntr": sorted_cntr,
        "u": sorted_u,
        "labels": sorted_labels,
        "xb": xb
    }

# ==============================================================================
# OPSI MENU 1: EKSEKUSI FCM & XIE-BENI INTERAKTIF
# ==============================================================================
def menu_fcm_xie_beni(datasets):
    print("\n" + "="*60)
    print(" 🛠️  PENGUJIAN ALGORITMA FUZZY C-MEANS & XIE-BENI INDEX")
    print("="*60)
    
    print("Pilih Kategori Dataset:")
    print(" 1. Tempat Wisata")
    print(" 2. Akomodasi (Hotel)")
    print(" 3. Kuliner (Tempat Makan)")
    cat_choice = input("Masukkan pilihan (1-3): ").strip()
    
    cat_map = {"1": "wisata", "2": "hotel", "3": "kuliner"}
    cat_name = cat_map.get(cat_choice, "wisata")
    df = datasets[cat_name].copy()
    
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
    
    xb, sigma, sep = calculate_xie_beni(prices, centers, U, m=m)
    
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
    
    print("\nPilih Tipe Analisis FCM:")
    print(" 1. Standard FCM (Percentile/Unanchored)")
    print(" 2. Budget-Anchored FCM (Berbasis Budget & Centroid Terpandu)")
    fcm_type = input("Pilih tipe (1-2, default 1): ").strip()
    
    c_range = [2, 3, 4, 5]
    best_c = 3
    min_xb = float('inf')
    
    # Rincian inisialisasi dinamis untuk Budget-Anchored FCM c = 2 s/d 5
    anchored_ratios = {
        2: [0.8, 1.2],
        3: None,  # Diambil dari RATIO_SCHEMES
        4: [0.5, 0.8, 1.2, 1.5],
        5: [0.4, 0.7, 1.0, 1.3, 1.6]
    }
    
    if fcm_type == "2":
        try:
            budget = float(input("\nMasukkan Total Budget (Rupiah, contoh 1500000): ") or 1500000)
            persons = int(input("Masukkan Jumlah Peserta (orang, default 2): ") or 2)
            duration = int(input("Masukkan Durasi Liburan (hari, default 2): ") or 2)
            
            print("\nSkema Rasio Centroid Inisialisasi (khusus untuk c=3):")
            for code, ratio in RATIO_SCHEMES.items():
                print(f"  [{code}] : Hemat={ratio[0]}x, Balanced={ratio[1]}x, Premium={ratio[2]}x")
            scheme_choice = input("Pilih Skema Rasio Centroid (A-E, default B): ").strip().upper()
            if scheme_choice not in RATIO_SCHEMES:
                scheme_choice = "B"
        except ValueError:
            print("❌ Input tidak valid! Menggunakan nilai default.")
            budget = 1500000
            persons = 2
            duration = 2
            scheme_choice = "B"
            
        # Alokasikan budget
        if duration == 1:
            allocations = {
                "akomodasi": 0.0,
                "wisata": budget * (15.0 / 60.0),
                "kuliner": budget * (20.0 / 60.0),
                "transportasi": budget * (25.0 / 60.0),
            }
        else:
            allocations = {
                "akomodasi": budget * 0.40,
                "wisata": budget * 0.15,
                "kuliner": budget * 0.20,
                "transportasi": budget * 0.25,
            }
            
        num_rooms = math.ceil(persons / 2.0)
        nights = duration - 1
        
        if cat_name == "hotel":
            if duration == 1:
                cat_anchor = (budget * 0.40) / (1 * num_rooms)
            else:
                cat_anchor = allocations["akomodasi"] / np.fmax(nights * num_rooms, 1.0)
        elif cat_name == "wisata":
            cat_anchor = allocations["wisata"] / persons
        else:
            cat_anchor = allocations["kuliner"] / (persons * 3 * duration)
            
        print(f"\n⚡ Budget Terdistribusi untuk {cat_name.upper()}: Rp {allocations['akomodasi'] if cat_name == 'hotel' else (allocations['wisata'] if cat_name == 'wisata' else allocations['kuliner']):,.0f}")
        print(f"🎯 Target Anggaran Mikro (Anchor) {cat_name.upper()} : Rp {cat_anchor:,.0f}/unit")
        print(f"\n🔄 Memulai simulasi BUDGET-ANCHORED FCM untuk {cat_name.upper()}...")
    else:
        print(f"\n🔄 Memulai simulasi STANDARD FCM (Percentile) untuk {cat_name.upper()}...")
        
    print("-" * 105)
    print(f"{'c':<4} | {'Xie-Beni Index':<16} | {'Total Variansi (σ)':<18} | {'Separasi (sep)':<14} | {'Centroid Awal (Initial)':<40}")
    print("-" * 105)
    
    for c in c_range:
        if fcm_type == "2":
            # Siapkan centroid awal berbasis ratio anchor
            if c == 3:
                ratios = RATIO_SCHEMES[scheme_choice]
            else:
                ratios = anchored_ratios[c]
                
            init_centers = np.array([cat_anchor * r for r in ratios]).reshape(-1, 1)
            init_centers_flat = init_centers.flatten()
            
            centers, U, labels, iters = fuzzy_c_means_manual(prices, n_clusters=c, m=2.0, init_centroids=init_centers)
        else:
            # Standar Percentile FCM
            q_vals = np.linspace(15, 85, c)
            init_centers_flat = np.percentile(prices, q_vals)
            centers, U, labels, iters = fuzzy_c_means_manual(prices, n_clusters=c, m=2.0, init_centroids=init_centers_flat)
            
        xb, sigma, sep = calculate_xie_beni(prices, centers, U, m=2.0)
        
        init_centers_str = ", ".join([f"Rp {v:,.0f}" for v in sorted(init_centers_flat)])
        print(f"{c:<4} | {xb:<16.6f} | {sigma:<18,.2f} | {sep:<14,.2f} | [{init_centers_str}]")
        
        if xb < min_xb:
            min_xb = xb
            best_c = c
            
    print("-" * 105)
    print(f"🌟 KLASTER OPTIMAL KATEGORI {cat_name.upper()} ADALAH c = {best_c}")
    print(f"   (Memiliki Nilai Xie-Beni Index terkecil yaitu {min_xb:.6f})")
    print("-" * 105)

# ==============================================================================
# OPSI MENU 3: BUDGET-FIRST WORKFLOW (SINKRON 100% DENGAN RECOMMENDER.PY)
# ==============================================================================
def menu_recommendation(datasets):
    print("\n" + "="*60)
    print(" 🎯 SISTEM REKOMENDASI PAKET WISATA (BUDGET-FIRST WORKFLOW)")
    print("="*60)
    
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
        
    print(f"\n⚡ Mendistribusikan Budget Rp {budget:,.0f} secara proporsional...")
    
    if duration == 1:
        allocations = {
            "akomodasi": 0.0,
            "wisata": budget * (15.0 / 60.0),
            "kuliner": budget * (20.0 / 60.0),
            "transportasi": budget * (25.0 / 60.0),
        }
    else:
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
    
    num_rooms = math.ceil(persons / 2.0)
    nights = duration - 1
    
    if duration == 1:
        hotel_anchor = (budget * 0.40) / (1 * num_rooms)
    else:
        hotel_anchor = allocations["akomodasi"] / np.fmax(nights * num_rooms, 1.0)
        
    wisata_anchor = allocations["wisata"] / persons
    kuliner_anchor = allocations["kuliner"] / (persons * 3 * duration)
    
    # --------------------------------------------------------------------------
    # SIMULASI & PERBANDINGAN XIE-BENI SECARA DINAMIS (c = 2 s/d 5)
    # --------------------------------------------------------------------------
    print("\n🔄 Menganalisis Jumlah Klaster Optimal (c = 2 s/d 5) secara Real-Time...")
    print("-" * 85)
    print(f"{'c':<4} | {'Wisata XBI':<14} | {'Hotel XBI':<14} | {'Kuliner XBI':<14} | {'Rata-rata XBI':<16}")
    print("-" * 85)
    
    best_c_auto = 3
    min_avg_xb = float('inf')
    xbi_results = {}
    
    for c_val in [2, 3, 4, 5]:
        xb_wisata = run_budget_anchored_fcm(datasets["wisata"]["Estimasi_Harga"].values, wisata_anchor, ratio_scheme=scheme_choice, n_clusters=c_val)["xb"]
        xb_hotel = run_budget_anchored_fcm(datasets["hotel"]["Estimasi_Harga"].values, hotel_anchor, ratio_scheme=scheme_choice, n_clusters=c_val)["xb"]
        xb_kuliner = run_budget_anchored_fcm(datasets["kuliner"]["Estimasi_Harga"].values, kuliner_anchor, ratio_scheme=scheme_choice, n_clusters=c_val)["xb"]
        
        avg_xb = (xb_wisata + xb_hotel + xb_kuliner) / 3.0
        xbi_results[c_val] = (xb_wisata, xb_hotel, xb_kuliner, avg_xb)
        
        if avg_xb < min_avg_xb:
            min_avg_xb = avg_xb
            best_c_auto = c_val
            
    for c_val, vals in xbi_results.items():
        w_xb, h_xb, k_xb, avg_xb = vals
        star = " ★ (Terbaik)" if c_val == best_c_auto else ""
        print(f"{c_val:<4} | {w_xb:<14.6f} | {h_xb:<14.6f} | {k_xb:<14.6f} | {avg_xb:<16.6f}{star}")
        
    print("-" * 85)
    print(f"📌 Secara akademis (XBI Terkecil), jumlah klaster terbaik adalah c = {best_c_auto} (Rata-rata XBI: {min_avg_xb:.6f}).")
    
    while True:
        try:
            chosen_c = input(f"👉 Masukkan jumlah klaster (c) yang ingin Anda gunakan (2-5, default {best_c_auto}): ").strip()
            if not chosen_c:
                chosen_c = best_c_auto
            chosen_c = int(chosen_c)
            if chosen_c in [2, 3, 4, 5]:
                break
            else:
                print("❌ Masukkan angka antara 2 s/d 5!")
        except ValueError:
            print("❌ Input tidak valid! Masukkan angka antara 2 s/d 5.")
            
    print(f"\n🔄 Menjalankan clustering dengan c = {chosen_c} klaster...")
    
    candidates = {
        "hotel": {i: [] for i in range(chosen_c)},
        "wisata": {i: [] for i in range(chosen_c)},
        "kuliner": {i: [] for i in range(chosen_c)}
    }
    
    for key in ["hotel", "wisata", "kuliner"]:
        df = datasets[key].copy()
        prices = df["Estimasi_Harga"].values
        cat_anchor = hotel_anchor if key == "hotel" else (wisata_anchor if key == "wisata" else kuliner_anchor)
        
        res = run_budget_anchored_fcm(prices, cat_anchor, ratio_scheme=scheme_choice, n_clusters=chosen_c)
        df["Cluster"] = res["labels"]
        print(f"   • [Clustering {key.upper()}] Xie-Beni Index (XBI): {res['xb']:.6f} | Centroids: {['Rp {:,.0f}'.format(c) for c in res['cntr']]}")
        
        if chosen_c == 3:
            ratios = RATIO_SCHEMES[scheme_choice]
        elif chosen_c == 2:
            ratios = [0.8, 1.2]
        elif chosen_c == 4:
            ratios = [0.5, 0.8, 1.2, 1.5]
        elif chosen_c == 5:
            ratios = [0.4, 0.7, 1.0, 1.3, 1.6]
        else:
            ratios = np.linspace(0.5, 1.5, chosen_c)
            
        for i in range(chosen_c):
            items_in_c = df[df["Cluster"] == i].copy()
            target_price = cat_anchor * ratios[i]
            
            if items_in_c.empty:
                df["distance_to_target"] = (df["Estimasi_Harga"] - target_price).abs()
                best_items = df.nsmallest(15, "distance_to_target")
            else:
                items_in_c["distance_to_target"] = (items_in_c["Estimasi_Harga"] - target_price).abs()
                best_items = items_in_c.nsmallest(15, "distance_to_target")
                
            candidates[key][i] = best_items.to_dict("records")
            
    package_options = {i: [] for i in range(chosen_c)}
    max_options_to_show = {i: 15 for i in range(chosen_c)}
    
    for i in range(chosen_c):
        hotel_list = candidates["hotel"][i]
        wisata_list = candidates["wisata"][i]
        kuliner_list = candidates["kuliner"][i]
        
        valid_combinations = []
        
        for h in hotel_list:
            for w in wisata_list:
                for k in kuliner_list:
                    cost_hotel = h["Estimasi_Harga"] * nights * num_rooms if duration > 1 else 0
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
                        
        def get_val(item, key, default=0.0):
            val = item.get(key, default)
            return default if (pd.isna(val) or val is None) else float(val)

        if i == 0:
            valid_combinations = sorted(valid_combinations, key=lambda x: x["total_dist"])
        elif i == chosen_c - 1:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating"), -get_val(x["hotel"], "Estimasi_Harga"), x["total_dist"])
            )
        else:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating") * 10 - get_val(x["kuliner"], "Rating") * 2 + x["total_dist"] / 10.0)
            )
        
        # Fallback jika kosong (diselaraskan dengan recommender.py & uji_gabungan.py)
        if not valid_combinations:
            min_cost_comb = None
            min_cost = float('inf')
            for h in hotel_list[:5]:
                for w in wisata_list[:5]:
                    for k in kuliner_list[:5]:
                        cost_hotel = h["Estimasi_Harga"] * nights * num_rooms if duration > 1 else 0
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
                
        package_options[i] = valid_combinations[:max_options_to_show[i]]
        
    # Tampilkan ke Terminal
    print("\n" + "="*60)
    print(" 📦  HASIL REKOMENDASI PAKET WISATA MULTI-OPSI (SPASIAL OPTIMIZED)")
    print("="*60)
    
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
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

    # Ekspor ke Excel
    excel_rows = []
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
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
# OPSI MENU 4: FLEXIBLE EXPLORATION WORKFLOW (SINKRON 100% DENGAN RECOMMENDER.PY)
# ==============================================================================
def menu_flexible_exploration(datasets):
    print("\n" + "="*60)
    print(" 🎯 SISTEM REKOMENDASI PAKET WISATA (FLEXIBLE EXPLORATION WORKFLOW)")
    print("="*60)
    
    try:
        persons = int(input("Masukkan Jumlah Peserta (orang, default 2): ") or 2)
        duration = int(input("Masukkan Durasi Liburan (hari, default 2): ") or 2)
    except ValueError:
        print("❌ Masukan tidak valid! Menggunakan nilai default.")
        persons = 2
        duration = 2
        
    # --------------------------------------------------------------------------
    # SIMULASI & PERBANDINGAN XIE-BENI SECARA DINAMIS (c = 2 s/d 5)
    # --------------------------------------------------------------------------
    print("\n🔄 Menganalisis Jumlah Klaster Optimal (c = 2 s/d 5) secara Real-Time...")
    print("-" * 85)
    print(f"{'c':<4} | {'Wisata XBI':<14} | {'Hotel XBI':<14} | {'Kuliner XBI':<14} | {'Rata-rata XBI':<16}")
    print("-" * 85)
    
    best_c_auto = 3
    min_avg_xb = float('inf')
    xbi_results = {}
    
    for c_val in [2, 3, 4, 5]:
        xb_wisata = run_percentile_fcm(datasets["wisata"]["Estimasi_Harga"].values, n_clusters=c_val)["xb"]
        xb_hotel = run_percentile_fcm(datasets["hotel"]["Estimasi_Harga"].values, n_clusters=c_val)["xb"]
        xb_kuliner = run_percentile_fcm(datasets["kuliner"]["Estimasi_Harga"].values, n_clusters=c_val)["xb"]
        
        avg_xb = (xb_wisata + xb_hotel + xb_kuliner) / 3.0
        xbi_results[c_val] = (xb_wisata, xb_hotel, xb_kuliner, avg_xb)
        
        if avg_xb < min_avg_xb:
            min_avg_xb = avg_xb
            best_c_auto = c_val
            
    for c_val, vals in xbi_results.items():
        w_xb, h_xb, k_xb, avg_xb = vals
        star = " ★ (Terbaik)" if c_val == best_c_auto else ""
        print(f"{c_val:<4} | {w_xb:<14.6f} | {h_xb:<14.6f} | {k_xb:<14.6f} | {avg_xb:<16.6f}{star}")
        
    print("-" * 85)
    print(f"📌 Secara akademis (XBI Terkecil), jumlah klaster terbaik adalah c = {best_c_auto} (Rata-rata XBI: {min_avg_xb:.6f}).")
    
    while True:
        try:
            chosen_c = input(f"👉 Masukkan jumlah klaster (c) yang ingin Anda gunakan (2-5, default {best_c_auto}): ").strip()
            if not chosen_c:
                chosen_c = best_c_auto
            chosen_c = int(chosen_c)
            if chosen_c in [2, 3, 4, 5]:
                break
            else:
                print("❌ Masukkan angka antara 2 s/d 5!")
        except ValueError:
            print("❌ Input tidak valid! Masukkan angka antara 2 s/d 5.")
            
    print(f"\n🔄 Menjalankan clustering dengan c = {chosen_c} klaster...")
    
    clustered = {}
    for cat_name in ["hotel", "wisata", "kuliner"]:
        df = datasets[cat_name].copy()
        prices = df["Estimasi_Harga"].values
        res = run_percentile_fcm(prices, n_clusters=chosen_c)
        df["Cluster"] = res["labels"]
        print(f"   • [Clustering {cat_name.upper()}] Xie-Beni Index (XBI): {res['xb']:.6f} | Centroids: {['Rp {:,.0f}'.format(c) for c in res['cntr']]}")
        # Hitung membership degree untuk sorting terdekat
        u_matrix = res["u"]
        df["Membership_Degree"] = [float(u_matrix[res["labels"][j], j]) for j in range(len(prices))]
        clustered[cat_name] = {"df": df, "cntr": res["cntr"]}
        
    candidates = {
        "hotel": {i: [] for i in range(chosen_c)},
        "wisata": {i: [] for i in range(chosen_c)},
        "kuliner": {i: [] for i in range(chosen_c)}
    }
    
    for key in ["hotel", "wisata", "kuliner"]:
        df = clustered[key]["df"]
        cntrs = clustered[key]["cntr"]
        for i in range(chosen_c):
            items_in_c = df[df["Cluster"] == i].copy()
            if items_in_c.empty:
                df["distance_to_target"] = (df["Estimasi_Harga"] - cntrs[i]).abs()
                best_items = df.nsmallest(15, "distance_to_target")
            else:
                best_items = items_in_c.sort_values(by="Membership_Degree", ascending=False).head(15)
                
            candidates[key][i] = best_items.to_dict("records")
            
    package_options = {i: [] for i in range(chosen_c)}
    max_options_to_show = {i: 15 for i in range(chosen_c)}
    num_rooms = math.ceil(persons / 2.0)
    nights = duration - 1
    
    for i in range(chosen_c):
        hotel_list = candidates["hotel"][i]
        wisata_list = candidates["wisata"][i]
        kuliner_list = candidates["kuliner"][i]
        
        valid_combinations = []
        
        for h in hotel_list:
            for w in wisata_list:
                for k in kuliner_list:
                    cost_hotel = h["Estimasi_Harga"] * nights * num_rooms if duration > 1 else 0
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
                        "total_cost": total_pkg_cost
                    })
                    
        def get_val(item, key, default=0.0):
            val = item.get(key, default)
            return default if (pd.isna(val) or val is None) else float(val)

        if i == 0:
            valid_combinations = sorted(valid_combinations, key=lambda x: x["total_dist"])
        elif i == chosen_c - 1:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating"), -get_val(x["hotel"], "Estimasi_Harga"), x["total_dist"])
            )
        else:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["wisata"], "Rating") * 10 - get_val(x["kuliner"], "Rating") * 2 + x["total_dist"] / 10.0)
            )
            
        package_options[i] = valid_combinations[:max_options_to_show[i]]
        
    print("\n" + "="*60)
    print(" 📦  HASIL REKOMENDASI FLEXIBLE EXPLORATION (KLASTER PERSENTIL)")
    print("="*60)
    
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
        options = package_options[i]
        
        print(f"\n=======================================================")
        print(f" 💼 KELAS PAKET: {label.upper()} (Menyajikan {len(options)} Opsi Terdekat)")
        print(f"=======================================================")
        
        for idx, opt in enumerate(options):
            h_item = opt["hotel"]
            w_item = opt["wisata"]
            k_item = opt["kuliner"]
            
            if duration > 1:
                hotel_detail = f"{h_item['Nama_Tempat']} (Rp {h_item['Estimasi_Harga']:,.0f}/malam)"
            else:
                hotel_detail = "Tanpa Hotel (One Day Trip)"
                
            print(f"\n 📦 OPSI {idx+1}")
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
            print("-" * 55)

    # Ekspor ke Excel
    excel_rows = []
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
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
                "Total Budget Input": "N/A (Flexible Exploration)",
                "Sisa Anggaran": 0,
                "Kelebihan Anggaran": 0,
                "Status": "FLEXIBLE EXPLORATION"
            })
            
    if excel_rows:
        try:
            export_df = pd.DataFrame(excel_rows)
            output_filename = "rekomendasi_paket_flexible.xlsx"
            export_df.to_excel(output_filename, index=False)
            print(f"\n💾  BERHASIL: Hasil rekomendasi Flexible telah diekspor ke Excel!")
            print(f"   📂 File tersimpan di: {os.path.abspath(output_filename)}")
        except Exception as e:
            print(f"\n❌ Gagal mengekspor hasil ke Excel: {e}")

# ==============================================================================
# OPSI MENU 5: DESTINATION-FIRST WORKFLOW (SINKRON 100% DENGAN RECOMMENDER.PY)
# ==============================================================================
def menu_destination_first(datasets):
    df_wisata = datasets["wisata"]
    print("\n" + "="*60)
    print(" 🎯  DESTINATION-FIRST WORKFLOW (SINKRON RECOMMENDER.PY)")
    print("="*60)
    print("\nReferensi 10 Destinasi Wisata Terpopuler (Rating Tertinggi):")
    print("-" * 75)
    print(f"{'ID':<6} | {'Nama Destinasi':<35} | {'Harga Tiket':<15} | {'Rating':<6}")
    print("-" * 75)
    
    if "Rating" in df_wisata.columns:
        top_spots = df_wisata.sort_values(by="Rating", ascending=False).head(10)
    else:
        top_spots = df_wisata.head(10)
        
    for _, row in top_spots.iterrows():
        rating_val = row["Rating"] if "Rating" in row and not pd.isna(row["Rating"]) else 0.0
        print(f"{int(row['Id_Tempat']):<6} | {row['Nama_Tempat'][:35]:<35} | Rp {row['Estimasi_Harga']:<12,.0f} | {rating_val:<6.1f}")
    print("-" * 75)
    
    while True:
        try:
            target_id = int(input("\n👉 Masukkan ID Tempat Wisata Pilihan Anda (bebas dari dataset Anda): ") or 0)
            dest_row = df_wisata[df_wisata["Id_Tempat"] == target_id]
            if not dest_row.empty:
                selected_dest = dest_row.iloc[0].to_dict()
                break
            else:
                print("❌ ID Tempat tidak ditemukan! Silakan periksa kembali dan masukkan ID yang valid.")
        except ValueError:
            print("❌ Input tidak valid! Harap masukkan angka ID Tempat.")
            
    print(f"\n📌 Destinasi Utama Terkunci: {selected_dest['Nama_Tempat']}")
    print(f"   • Tiket Satuan : Rp {selected_dest['Estimasi_Harga']:,.0f}")
    print(f"   • Koordinat    : ({selected_dest['Latitude']}, {selected_dest['Longitude']})")
    
    print("\nPilih Kondisi Operasional:")
    print(" 1. Kondisi A (Dengan Input Budget & Validasi Finansial)")
    print(" 2. Kondisi B (Tanpa Input Budget & Eksplorasi Spasial Klaster)")
    
    while True:
        cond_choice = input("Pilih kondisi (1 atau 2): ").strip()
        if cond_choice in ["1", "2"]:
            break
        print("❌ Pilihan tidak valid! Silakan masukkan 1 atau 2.")
        
    try:
        persons = int(input("\nMasukkan Jumlah Peserta (orang, default 2): ") or 2)
        duration = int(input("Masukkan Durasi Liburan (hari, default 2): ") or 2)
    except ValueError:
        persons = 2
        duration = 2
        
    num_rooms = math.ceil(persons / 2.0)
    nights = duration - 1
    tiket_total = selected_dest["Estimasi_Harga"] * persons
    
    clustered = {}
    
    if cond_choice == "2":
        # Kondisi B: Tanpa Budget (Percentile Offline)
        # --------------------------------------------------------------------------
        # SIMULASI & PERBANDINGAN XIE-BENI SECARA DINAMIS (c = 2 s/d 5) - KONDISI B
        # --------------------------------------------------------------------------
        print("\n🔄 Menganalisis Jumlah Klaster Optimal (c = 2 s/d 5) secara Real-Time...")
        print("-" * 70)
        print(f"{'c':<4} | {'Hotel XBI':<14} | {'Kuliner XBI':<14} | {'Rata-rata XBI':<16}")
        print("-" * 70)
        
        best_c_auto = 3
        min_avg_xb = float('inf')
        xbi_results = {}
        
        for c_val in [2, 3, 4, 5]:
            xb_hotel = run_percentile_fcm(datasets["hotel"]["Estimasi_Harga"].values, n_clusters=c_val)["xb"]
            xb_kuliner = run_percentile_fcm(datasets["kuliner"]["Estimasi_Harga"].values, n_clusters=c_val)["xb"]
            
            avg_xb = (xb_hotel + xb_kuliner) / 2.0
            xbi_results[c_val] = (xb_hotel, xb_kuliner, avg_xb)
            
            if avg_xb < min_avg_xb:
                min_avg_xb = avg_xb
                best_c_auto = c_val
                
        for c_val, vals in xbi_results.items():
            h_xb, k_xb, avg_xb = vals
            star = " ★ (Terbaik)" if c_val == best_c_auto else ""
            print(f"{c_val:<4} | {h_xb:<14.6f} | {k_xb:<14.6f} | {avg_xb:<16.6f}{star}")
            
        print("-" * 70)
        print(f"📌 Secara akademis (XBI Terkecil), jumlah klaster terbaik adalah c = {best_c_auto} (Rata-rata XBI: {min_avg_xb:.6f}).")
        
        while True:
            try:
                chosen_c = input(f"👉 Masukkan jumlah klaster (c) yang ingin Anda gunakan (2-5, default {best_c_auto}): ").strip()
                if not chosen_c:
                    chosen_c = best_c_auto
                chosen_c = int(chosen_c)
                if chosen_c in [2, 3, 4, 5]:
                    break
                else:
                    print("❌ Masukkan angka antara 2 s/d 5!")
            except ValueError:
                print("❌ Input tidak valid! Masukkan angka antara 2 s/d 5.")
                
        print(f"\n🔄 Menjalankan clustering dengan c = {chosen_c} klaster...")
        
        for cat_name in ["hotel", "kuliner"]:
            df = datasets[cat_name].copy()
            prices = df["Estimasi_Harga"].values
            res = run_percentile_fcm(prices, n_clusters=chosen_c)
            df["Cluster"] = res["labels"]
            print(f"   • [Clustering {cat_name.upper()}] Xie-Beni Index (XBI): {res['xb']:.6f} | Centroids: {['Rp {:,.0f}'.format(c) for c in res['cntr']]}")
            # Hitung membership
            u_matrix = res["u"]
            df["Membership_Degree"] = [float(u_matrix[res["labels"][j], j]) for j in range(len(prices))]
            clustered[cat_name] = {"df": df, "cntr": res["cntr"]}
            
    else:
        # Kondisi A: Dengan Budget (Real-Time FCM Anchor)
        try:
            budget = float(input("Masukkan Total Budget Anda (Rupiah, contoh 1500000): ") or 1500000)
        except ValueError:
            budget = 1500000
            
        sisa_budget = budget - tiket_total
        if sisa_budget <= 0:
            print(f"\n🚨 WARNING: Anggaran Anda (Rp {budget:,.0f}) tidak mencukupi untuk tiket destinasi utama!")
            return
            
        if duration == 1:
            budget_hotel_total = sisa_budget * (40.0/85.0)
            budget_kul_total = sisa_budget * (20.0/45.0)
            anchor_hotel = budget_hotel_total / (1 * num_rooms)
        else:
            budget_hotel_total = sisa_budget * (40.0/85.0)
            budget_kul_total = sisa_budget * (20.0/85.0)
            anchor_hotel = budget_hotel_total / np.fmax(nights * num_rooms, 1.0)
            
        anchor_kul = budget_kul_total / (persons * 3 * duration)
        
        print(f"   • Sisa Anggaran Hotel per malam: Rp {anchor_hotel:,.0f}")
        print(f"   • Sisa Anggaran Kuliner per porsi: Rp {anchor_kul:,.0f}")
        
        # --------------------------------------------------------------------------
        # SIMULASI & PERBANDINGAN XIE-BENI SECARA DINAMIS (c = 2 s/d 5) - KONDISI A
        # --------------------------------------------------------------------------
        print("\n🔄 Menganalisis Jumlah Klaster Optimal (c = 2 s/d 5) secara Real-Time...")
        print("-" * 70)
        print(f"{'c':<4} | {'Hotel XBI':<14} | {'Kuliner XBI':<14} | {'Rata-rata XBI':<16}")
        print("-" * 70)
        
        best_c_auto = 3
        min_avg_xb = float('inf')
        xbi_results = {}
        
        for c_val in [2, 3, 4, 5]:
            xb_hotel = run_budget_anchored_fcm(datasets["hotel"]["Estimasi_Harga"].values, anchor_hotel, ratio_scheme="B", n_clusters=c_val)["xb"]
            xb_kuliner = run_budget_anchored_fcm(datasets["kuliner"]["Estimasi_Harga"].values, anchor_kul, ratio_scheme="B", n_clusters=c_val)["xb"]
            
            avg_xb = (xb_hotel + xb_kuliner) / 2.0
            xbi_results[c_val] = (xb_hotel, xb_kuliner, avg_xb)
            
            if avg_xb < min_avg_xb:
                min_avg_xb = avg_xb
                best_c_auto = c_val
                
        for c_val, vals in xbi_results.items():
            h_xb, k_xb, avg_xb = vals
            star = " ★ (Terbaik)" if c_val == best_c_auto else ""
            print(f"{c_val:<4} | {h_xb:<14.6f} | {k_xb:<14.6f} | {avg_xb:<16.6f}{star}")
            
        print("-" * 70)
        print(f"📌 Secara akademis (XBI Terkecil), jumlah klaster terbaik adalah c = {best_c_auto} (Rata-rata XBI: {min_avg_xb:.6f}).")
        
        while True:
            try:
                chosen_c = input(f"👉 Masukkan jumlah klaster (c) yang ingin Anda gunakan (2-5, default {best_c_auto}): ").strip()
                if not chosen_c:
                    chosen_c = best_c_auto
                chosen_c = int(chosen_c)
                if chosen_c in [2, 3, 4, 5]:
                    break
                else:
                    print("❌ Masukkan angka antara 2 s/d 5!")
            except ValueError:
                print("❌ Input tidak valid! Masukkan angka antara 2 s/d 5.")
                
        print(f"\n🔄 Menjalankan clustering dengan c = {chosen_c} klaster...")
        
        for cat_name, anchor in [("hotel", anchor_hotel), ("kuliner", anchor_kul)]:
            df = datasets[cat_name].copy()
            prices = df["Estimasi_Harga"].values
            res = run_budget_anchored_fcm(prices, anchor, ratio_scheme="B", n_clusters=chosen_c)
            df["Cluster"] = res["labels"]
            print(f"   • [Clustering {cat_name.upper()}] Xie-Beni Index (XBI): {res['xb']:.6f} | Centroids: {['Rp {:,.0f}'.format(c) for c in res['cntr']]}")
            # Hitung membership
            u_matrix = res["u"]
            df["Membership_Degree"] = [float(u_matrix[res["labels"][j], j]) for j in range(len(prices))]
            clustered[cat_name] = {"df": df, "cntr": res["cntr"]}
            
    candidates = {
        "hotel": {i: [] for i in range(chosen_c)},
        "kuliner": {i: [] for i in range(chosen_c)}
    }
    
    if chosen_c == 3:
        ratios = RATIO_SCHEMES["B"]
    elif chosen_c == 2:
        ratios = [0.8, 1.2]
    elif chosen_c == 4:
        ratios = [0.5, 0.8, 1.2, 1.5]
    elif chosen_c == 5:
        ratios = [0.4, 0.7, 1.0, 1.3, 1.6]
    else:
        ratios = np.linspace(0.5, 1.5, chosen_c)
        
    for key in ["hotel", "kuliner"]:
        df = clustered[key]["df"]
        cntrs = clustered[key]["cntr"]
        
        if cond_choice == "1":
            anchor = anchor_hotel if key == "hotel" else anchor_kul
        else:
            anchor = None
            
        for i in range(chosen_c):
            items_in_c = df[df["Cluster"] == i].copy()
            target_price = anchor * ratios[i] if anchor is not None else cntrs[i]
            
            if items_in_c.empty:
                df["distance_to_target"] = (df["Estimasi_Harga"] - target_price).abs()
                best_items = df.nsmallest(15, "distance_to_target")
            else:
                items_in_c["distance_to_target"] = (items_in_c["Estimasi_Harga"] - target_price).abs()
                best_items = items_in_c.nsmallest(15, "distance_to_target")
                
            candidates[key][i] = best_items.to_dict("records")
            
    package_options = {i: [] for i in range(chosen_c)}
    max_options_to_show = {i: 15 for i in range(chosen_c)}
    
    for i in range(chosen_c):
        hotel_list = candidates["hotel"][i]
        kuliner_list = candidates["kuliner"][i]
        
        valid_combinations = []
        for h in hotel_list:
            for k in kuliner_list:
                cost_hotel = h["Estimasi_Harga"] * nights * num_rooms if duration > 1 else 0
                cost_wisata = tiket_total
                cost_kuliner = k["Estimasi_Harga"] * persons * 3 * duration
                
                if duration == 1:
                    d1 = haversine_distance(k["Latitude"], k["Longitude"], selected_dest["Latitude"], selected_dest["Longitude"])
                    total_dist = d1 * 2
                else:
                    d1 = haversine_distance(h["Latitude"], h["Longitude"], selected_dest["Latitude"], selected_dest["Longitude"])
                    d2 = haversine_distance(selected_dest["Latitude"], selected_dest["Longitude"], k["Latitude"], k["Longitude"])
                    d3 = haversine_distance(k["Latitude"], k["Longitude"], h["Latitude"], h["Longitude"])
                    total_dist = d1 + d2 + d3
                    
                cost_transport, transport_desc = get_transport_info(persons, total_dist)
                total_pkg_cost = cost_hotel + cost_wisata + cost_kuliner + cost_transport
                
                if cond_choice == "2" or total_pkg_cost <= budget:
                    valid_combinations.append({
                        "hotel": h,
                        "wisata": selected_dest,
                        "kuliner": k,
                        "cost_hotel": cost_hotel,
                        "cost_wisata": cost_wisata,
                        "cost_kuliner": cost_kuliner,
                        "cost_transport": cost_transport,
                        "transport_desc": transport_desc,
                        "total_dist": total_dist,
                        "total_cost": total_pkg_cost,
                        "selisih": (budget - total_pkg_cost) if cond_choice == "1" else 0.0
                    })
                    
        def get_val(item, key, default=0.0):
            val = item.get(key, default)
            return default if (pd.isna(val) or val is None) else float(val)

        if i == 0:
            valid_combinations = sorted(valid_combinations, key=lambda x: x["total_dist"])
        elif i == chosen_c - 1:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["hotel"], "Estimasi_Harga"), x["total_dist"])
            )
        else:
            valid_combinations = sorted(
                valid_combinations,
                key=lambda x: (-get_val(x["kuliner"], "Rating") * 5 + x["total_dist"] / 10.0)
            )
            
        # Fallback jika kosong (hanya berlaku jika pakai budget / Kondisi A)
        if cond_choice == "1" and not valid_combinations:
            min_cost_comb = None
            min_cost = float('inf')
            for h in hotel_list[:5]:
                for k in kuliner_list[:5]:
                    cost_hotel = h["Estimasi_Harga"] * nights * num_rooms if duration > 1 else 0
                    cost_wisata = tiket_total
                    cost_kuliner = k["Estimasi_Harga"] * persons * 3 * duration
                    if duration == 1:
                        d1 = haversine_distance(k["Latitude"], k["Longitude"], selected_dest["Latitude"], selected_dest["Longitude"])
                        total_dist = d1 * 2
                    else:
                        d1 = haversine_distance(h["Latitude"], h["Longitude"], selected_dest["Latitude"], selected_dest["Longitude"])
                        d2 = haversine_distance(selected_dest["Latitude"], selected_dest["Longitude"], k["Latitude"], k["Longitude"])
                        d3 = haversine_distance(k["Latitude"], k["Longitude"], h["Latitude"], h["Longitude"])
                        total_dist = d1 + d2 + d3
                    cost_transport, transport_desc = get_transport_info(persons, total_dist)
                    total_pkg_cost = cost_hotel + cost_wisata + cost_kuliner + cost_transport
                    if total_pkg_cost < min_cost:
                        min_cost = total_pkg_cost
                        min_cost_comb = {
                            "hotel": h,
                            "wisata": selected_dest,
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
                
        package_options[i] = valid_combinations[:max_options_to_show[i]]
        
    print("\n" + "="*60)
    print(" 📦  HASIL REKOMENDASI DESTINATION-FIRST (SINKRON DENGAN RECOMMENDER.PY)")
    print("="*60)
    
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
        options = package_options[i]
        
        print(f"\n=======================================================")
        print(f" 💼 KELAS PAKET: {label.upper()} (Menyajikan {len(options)} Opsi Terdekat)")
        print(f"=======================================================")
        
        for idx, opt in enumerate(options):
            h_item = opt["hotel"]
            w_item = opt["wisata"]
            k_item = opt["kuliner"]
            
            if cond_choice == "1":
                status = "✅ UNDER BUDGET" if opt["total_cost"] <= budget else "⚠️ OVER BUDGET"
            else:
                status = "EKSPLORASI SPASIAL (TANPA BUDGET)"
                
            if duration > 1:
                hotel_detail = f"{h_item['Nama_Tempat']} (Rp {h_item['Estimasi_Harga']:,.0f}/malam)"
            else:
                hotel_detail = "Tanpa Hotel (One Day Trip)"
                
            print(f"\n 📦 OPSI {idx+1} ({status})")
            print("-" * 55)
            print(f"  🏨 Hotel     : {hotel_detail}")
            if duration > 1:
                print(f"                 Rincian: Rp {h_item['Estimasi_Harga']:,.0f} x {nights} malam x {num_rooms} kamar = Rp {opt['cost_hotel']:,.0f}")
            print(f"  🎯 Wisata    : {w_item['Nama_Tempat']} (Tiket: Rp {w_item['Estimasi_Harga']:,.0f}/orang)")
            print(f"                 Rincian: Rp {w_item['Estimasi_Harga']:,.0f} x {persons} orang = Rp {opt['cost_wisata']:,.0f}")
            print(f"  🍜 Kuliner   : {k_item['Nama_Tempat']}")
            print(f"                 Rincian: Rp {k_item['Estimasi_Harga']:,.0f} x {persons} orang x 3 makan x {duration} hari = Rp {opt['cost_kuliner']:,.0f}")
            print(f"  🚗 Transport : Rp {opt['cost_transport']:,.0f}")
            print(f"                 Rincian: Rute {opt['total_dist']:.2f} km menggunakan {opt['transport_desc']}")
            print("-" * 55)
            print(f"  💰 ESTIMASI TOTAL BIAYA PAKET : Rp {opt['total_cost']:,.0f}")
            if cond_choice == "1":
                if opt["selisih"] >= 0:
                    print(f"  💵 Sisa Anggaran (Kembalian)  : Rp {opt['selisih']:,.0f}")
                else:
                    print(f"  💸 Kelebihan Anggaran (Nominal) : Rp {abs(opt['selisih']):,.0f}")
            print("-" * 55)

    # Ekspor ke Excel
    excel_rows = []
    for i in range(chosen_c):
        label = get_cluster_label(i, chosen_c)
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
                "Total Budget Input": budget if cond_choice == "1" else "N/A",
                "Sisa Anggaran": opt["selisih"] if (cond_choice == "1" and opt["selisih"] >= 0) else 0,
                "Kelebihan Anggaran": abs(opt["selisih"]) if (cond_choice == "1" and opt["selisih"] < 0) else 0,
                "Status": "UNDER BUDGET" if (cond_choice == "1" and opt["total_cost"] <= budget) else ("OVER BUDGET" if cond_choice == "1" else "DESTINATION EXPLORATION")
            })
            
    if excel_rows:
        try:
            export_df = pd.DataFrame(excel_rows)
            output_filename = "rekomendasi_paket_destination.xlsx"
            export_df.to_excel(output_filename, index=False)
            print(f"\n💾  BERHASIL: Hasil rekomendasi Destination-First telah diekspor ke Excel!")
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
    
    datasets = find_and_load_excel()
    
    while True:
        print("\nMENU PENGUJIAN ALGORITMA DI TERMINAL:")
        print("="*38)
        print(" 1. Run Algoritma FCM Manual & Hitung Xie-Beni Index")
        print(" 2. Pengujian Nilai c Optimal (2 s/d 5) via Xie-Beni Index")
        print(" 3. Simulasi Workflow Rekomendasi Paket Wisata (Budget-First)")
        print(" 4. Simulasi Workflow Rekomendasi Paket Wisata (Flexible Exploration)")
        print(" 5. Simulasi Workflow Rekomendasi Paket Wisata (Destination-First)")
        print(" 6. Keluar dari Program")
        print("="*38)
        
        choice = input("Pilih nomor menu (1-6): ").strip()
        
        if choice == "1":
            menu_fcm_xie_beni(datasets)
        elif choice == "2":
            menu_optimal_c_search(datasets)
        elif choice == "3":
            menu_recommendation(datasets)
        elif choice == "4":
            menu_flexible_exploration(datasets)
        elif choice == "5":
            menu_destination_first(datasets)
        elif choice == "6":
            print("\n👋 Keluar dari sistem pengujian. Terima kasih dan sukses skripsinya!")
            break
        else:
            print("\n❌ Pilihan menu tidak valid. Silakan pilih kembali (1-6).")


if __name__ == "__main__":
    main()
