import os
import pandas as pd
import numpy as np

# Path Configuration
BASE_DIR = "/Users/macbookpro/Documents/GITHUB/PROJET-SKRIPSI/PREPOCESSING"
DATA_DIR = os.path.join(BASE_DIR, "DATA&HTM-NEW")
RAW_WISATA_FILE = os.path.join(DATA_DIR, "htm-hotel.xlsx")

def custom_fcm(data, c, m=2.0, max_iter=150, error=1e-5):
    """
    Fuzzy C-Means (FCM) using NumPy.
    """
    n = data.shape[0]
    U = np.random.rand(n, c)
    U = U / np.sum(U, axis=1, keepdims=True)
    
    centroids = np.zeros((c, 1))
    
    for iteration in range(max_iter):
        U_prev = U.copy()
        
        # 1. Compute Centroids
        Um = U ** m
        centroids = np.sum(Um * data[:, np.newaxis], axis=0) / np.sum(Um, axis=0)
        
        # 2. Compute Distances
        distances = np.abs(data[:, np.newaxis] - centroids)
        distances = np.fmax(distances, 1e-10)
        
        # 3. Update Membership Matrix U
        for i in range(n):
            for k in range(c):
                denom = np.sum((distances[i, k] / distances[i, :]) ** (2 / (m - 1)))
                U[i, k] = 1.0 / denom
                
        if np.linalg.norm(U - U_prev) < error:
            break
            
    # Sort centroids
    idx = np.argsort(centroids)
    centroids = centroids[idx]
    U = U[:, idx]
    
    return centroids, U

def calculate_xie_beni(data, U, centroids, m=2.0):
    """
    Compute Xie-Beni Index.
    """
    n = data.shape[0]
    c = centroids.shape[0]
    
    # 1. Compactness
    total_variance = 0.0
    for k in range(c):
        diff = data - centroids[k]
        dist_sq = diff ** 2
        total_variance += np.sum((U[:, k] ** m) * dist_sq)
        
    # 2. Separation
    min_center_dist_sq = float('inf')
    for i in range(c):
        for j in range(i + 1, c):
            dist_sq = (centroids[i] - centroids[j]) ** 2
            if dist_sq < min_center_dist_sq:
                min_center_dist_sq = dist_sq
                
    # 3. Xie-Beni Index
    xb_index = total_variance / (n * min_center_dist_sq)
    return xb_index

def run_multi_cluster_experiment():
    print("="*80)
    print("🔬 EKSPERIMEN EVALUASI JUMLAH KLASTER (C=2 HINGGA C=5) PADA DATA MENTAH")
    print("="*80)
    
    # Load raw dataset (only drop NaN values)
    df_raw = pd.read_excel(RAW_WISATA_FILE).dropna(subset=['Estimasi_Harga'])
    raw_prices = df_raw['Estimasi_Harga'].values.astype(float)
    
    print(f"Jumlah sampel data wisata mentah: {len(raw_prices)}")
    print(f"Harga Minimum: Rp {int(np.min(raw_prices)):,}")
    print(f"Harga Maksimum: Rp {int(np.max(raw_prices)):,}")
    print(f"Harga Rata-rata: Rp {int(np.mean(raw_prices)):,}")
    print("="*80 + "\n")
    
    results = []
    
    # Run FCM for c = 2, 3, 4, 5
    for c in [2, 3, 4, 5]:
        print(f"-> Memproses Klastering untuk C = {c}... ", end="", flush=True)
        centroids, U = custom_fcm(raw_prices, c=c)
        xbi = calculate_xie_beni(raw_prices, U, centroids)
        print("Selesai.")
        
        results.append({
            'c': c,
            'centroids': centroids,
            'xbi': xbi
        })
        
    # Print Experimental Report
    print("\n" + "="*80)
    print("📊 LAPORAN EKSPERIMEN PERBANDINGAN NILAI XIE-BENI INDEX (XBI)")
    print("="*80)
    print(f"{'Jumlah Klaster (c)':<20} | {'Centroids Final (Rupiah)':<45} | {'Xie-Beni Index (XBI)'}")
    print("-"*85)
    
    for r in results:
        c_str = f"C = {r['c']}"
        centroids_formatted = " -> ".join([f"Rp {int(cen):,}" for cen in r['centroids']])
        print(f"{c_str:<20} | {centroids_formatted:<45} | {r['xbi']:.6f}")
        
    print("="*85)
    print("\n📝 ANALISIS STRATEGIS DOSEN PEMBIMBING:")
    print("="*80)
    print("1. Perhatikan pergeseran centroid saat jumlah klaster (C) bertambah.")
    print("2. Outlier ekstrem (Rp 1.800.000) selalu mendominasi klaster tertinggi di semua kondisi.")
    print("3. Analisis nilai Xie-Beni Index terkecil menunjukkan konfigurasi klaster yang paling optimal.")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_multi_cluster_experiment()
