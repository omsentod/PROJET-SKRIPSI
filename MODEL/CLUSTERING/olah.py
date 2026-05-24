import pandas as pd
import numpy as np
import os

# ALGORITMA FCM (CORE)

def fuzzy_c_means_manual(data, n_clusters=3, m=2, error=1e-5, max_iter=100):
    """
    Algoritma FCM Manual.
    Input 'data' adalah numpy array yang SUDAH dinormalisasi.
    """
    n_samples, n_features = data.shape
    
    np.random.seed(42) 
    U = np.random.dirichlet(np.ones(n_clusters), size=n_samples).T
    
    centers = np.zeros((n_clusters, n_features))
    
    for iteration in range(max_iter):
        U_prev = U.copy()
        

        for j in range(n_clusters):
            numerator = np.sum((U[j, :] ** m)[:, np.newaxis] * data, axis=0)
            denominator = np.sum(U[j, :] ** m)
            centers[j, :] = numerator / denominator
            
      
        dist_sq = np.zeros((n_clusters, n_samples))
        for j in range(n_clusters):
            dist_sq[j, :] = np.sum((data - centers[j, :])**2, axis=1)
            
        dist_sq = np.fmax(dist_sq, 1e-10)
        
        temp = dist_sq ** (-1 / (m - 1))
        denominator = np.sum(temp, axis=0)
        U = temp / denominator
        
        if np.linalg.norm(U - U_prev) < error:
            break
            
    return centers, U


def process_ready_data(filename, output_filename):
    print(f"🔄 Memproses data normalisasi: {filename} ...")
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} tidak ditemukan!\n")
        return

    try:
        # Baca Excel
        df = pd.read_excel(filename)
        

        norm_cols = ['Norm_Estimasi_Harga'] 
        
        for col in norm_cols:
            if col not in df.columns:
                raise ValueError(f"Kolom '{col}' tidak ditemukan!")
        
        data_matrix = df[norm_cols].values
        
        centers, U = fuzzy_c_means_manual(data_matrix, n_clusters=3, m=2)
        
        centroid_prices = centers[:, 0] 
        sorted_indices = np.argsort(centroid_prices) 
        

        print(f"\n📊 PUSAT CLUSTER (Nilai Normalisasi 0-1) untuk {filename}:")
        print("-" * 45)
        print(f"{'Kategori':<10} | {'Pusat Harga':<15}")
        print("-" * 45)
        
        labels = ['Murah', 'Sedang', 'Mahal']
        
        for i in range(3):
            idx_asli = sorted_indices[i]
            
            c_harga = centers[idx_asli, 0]
            
            print(f"{labels[i]:<10} | {c_harga:.6f}")
            
        print("-" * 45 + "\n")

        U = U.T 
        
        cols_membership = ['Mu_Murah', 'Mu_Sedang', 'Mu_Mahal']
        
        for i in range(3):
            original_cluster_idx = sorted_indices[i]
            df[cols_membership[i]] = U[:, original_cluster_idx]
            
        df['Cluster_FCM'] = df[cols_membership].idxmax(axis=1).str.replace('Mu_', '')
        
        df.to_excel(output_filename, index=False)
        print(f"✅ Selesai! Hasil disimpan di: {output_filename}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")


process_ready_data('dbset/wisata_normalized.xlsx', 'hasil_fcm_wisata.xlsx')
process_ready_data('dbset/hotel_normalized.xlsx', 'hasil_fcm_hotel.xlsx')
process_ready_data('dbset/makan_normalized.xlsx', 'hasil_fcm_makan.xlsx')