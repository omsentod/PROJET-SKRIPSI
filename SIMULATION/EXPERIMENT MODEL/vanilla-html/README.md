# Sistem Rekomendasi Wisata Malang - Vanilla HTML/CSS/JS

Ini adalah versi **HTML, CSS, dan JavaScript murni** dari aplikasi Sistem Rekomendasi Wisata Malang yang sebelumnya dibuat dengan React/TypeScript.

## 📁 Struktur File

```
vanilla-html/
├── index.html    # File HTML utama dengan template
├── styles.css    # Styling lengkap (mirip Tailwind CSS)
├── app.js        # Logika aplikasi & state management
└── README.md     # Dokumentasi ini
```

## 🚀 Cara Menjalankan

### Opsi 1: Langsung di Browser
1. Buka file `index.html` di browser favorit Anda
2. Aplikasi akan langsung berjalan tanpa perlu server

### Opsi 2: Menggunakan Live Server (Recommended)
1. Jika menggunakan VS Code, install extension "Live Server"
2. Klik kanan pada `index.html` → "Open with Live Server"
3. Aplikasi akan terbuka di browser dengan auto-reload

### Opsi 3: Menggunakan Python Server
```bash
# Python 3
python3 -m http.server 8000

# Atau Python 2
python -m SimpleHTTPServer 8000
```
Kemudian buka `http://localhost:8000` di browser

### Opsi 4: Menggunakan Node.js http-server
```bash
npx http-server -p 8000
```
Kemudian buka `http://localhost:8000` di browser

## ✨ Fitur Aplikasi

### 1. **Halaman Form (FormPage)**
- Input total anggaran dengan format rupiah otomatis
- Input jumlah peserta dengan tombol increment/decrement
- Input durasi liburan dengan tombol increment/decrement
- **Perhitungan otomatis:**
  - Budget per orang
  - Kebutuhan kamar hotel (1 kamar max 2 orang)
  - Kebutuhan makan (orang × hari × 3 kali)

### 2. **Halaman Hasil (ResultsPage)**
- Menampilkan 3 opsi paket wisata:
  - **HEMAT** - Untuk budget terbatas
  - **BALANCED** - Budget seimbang
  - **PREMIUM** - Budget lebih tinggi
- Setiap paket menampilkan:
  - Hotel dengan harga per malam
  - Tempat wisata dengan harga tiket
  - Tempat makan dengan harga per porsi
  - Koordinat lokasi untuk setiap tempat
  - Toggle rincian biaya (expand/collapse)
  - Total harga paket
  - Sisa anggaran (hijau jika cukup, merah jika kurang)
- Tombol "Lihat Detail & Peta" untuk setiap paket

### 3. **Halaman Detail (DetailPage)**
- Detail lengkap untuk paket yang dipilih
- Card visual untuk Hotel, Wisata, dan Makan dengan:
  - Gambar placeholder dengan gradien
  - Nama lengkap tempat
  - Harga detail
  - Koordinat GPS
  - Tombol copy koordinat
  - Link ke Google Maps
- Panel rincian biaya lengkap
- **Informasi jarak:**
  - Jarak Hotel → Wisata
  - Jarak Wisata → Makan  
  - Jarak Makan → Hotel
  - Total jarak tempuh
- **Peta interaktif** (mock SVG) dengan:
  - Pin lokasi berwarna (Hotel=Biru, Wisata=Hijau, Makan=Oranye)
  - Garis rute antar lokasi
  - Kontrol zoom in/out
  - Legend peta
- Tombol "Simpan Paket" dan "Kembali ke Pilihan"

## 🎨 Teknologi & Implementasi

### HTML
- Semantic HTML5
- Template element untuk reusable components
- Struktur yang clean dan terorganisir

### CSS
- **Utility-first approach** mirip Tailwind CSS
- CSS Variables untuk color theming
- Responsive design dengan media queries
- Smooth transitions dan hover effects
- Gradient backgrounds
- Shadow utilities

### JavaScript
- **Vanilla JavaScript** tanpa framework
- State management sederhana dengan object
- Dynamic rendering dengan DOM manipulation
- Event handling yang efisien
- Format currency Indonesia
- Perhitungan jarak koordinat (Haversine formula)
- Copy to clipboard functionality

## 📊 Data Paket

Aplikasi ini menggunakan data statis untuk 3 paket wisata:

### Paket Hemat (Rp 691.640)
- Hotel: SUPER OYO Flagship 90502 Holistay
- Wisata: Masjid Tiban Malang
- Makan: Depot Gang Djangkrik

### Paket Balanced (Rp 2.008.381)
- Hotel: OYO Life 91931 Permata Brantas
- Wisata: Makam Ki Ageng Gribig
- Makan: Resto 52

### Paket Premium (Rp 5.385.197)
- Hotel: Villa Malang MARRY IND Puncak Buring
- Wisata: Pura Luhur Giri Arjuno
- Makan: Harmoni Cafe & Resto

## 🔄 Perbedaan dengan Versi React

### Yang Sama:
✅ Semua fitur UI/UX identik  
✅ Styling visual yang mirip  
✅ Flow navigasi yang sama  
✅ Data dan perhitungan yang sama  

### Yang Berbeda:
- ❌ Tidak menggunakan React hooks (useState, useEffect)
- ❌ Tidak ada JSX, diganti dengan template literals
- ❌ Tidak ada TypeScript, murni JavaScript
- ❌ Tidak perlu build process atau bundler
- ❌ Tidak ada dependencies/node_modules
- ✅ Lebih ringan dan cepat di-load
- ✅ Bisa langsung dibuka di browser
- ✅ Lebih mudah di-deploy

## 🌐 Browser Compatibility

Aplikasi ini kompatibel dengan:
- ✅ Chrome/Edge (versi terbaru)
- ✅ Firefox (versi terbaru)
- ✅ Safari (versi terbaru)
- ✅ Opera (versi terbaru)

**Note:** Fitur copy to clipboard memerlukan HTTPS atau localhost

## 📝 Catatan Pengembangan

### State Management
State disimpan dalam object `appState` dengan properties:
- `currentPage`: 'form' | 'results' | 'detail'
- `budgetData`: { totalBudget, participants, duration }
- `selectedPackage`: 'hemat' | 'balanced' | 'premium'

### Rendering Pattern
Aplikasi menggunakan pattern:
1. Clear container (`app.innerHTML = ''`)
2. Create content (dari template atau dynamic)
3. Append to DOM
4. Setup event handlers
5. Scroll to top

### Event Delegation
Event handlers di-setup setelah rendering untuk menghindari memory leaks.

## 🎯 Kegunaan

Aplikasi ini cocok untuk:
- ✅ **Skripsi/Thesis** - Sebagai implementasi sistem rekomendasi
- ✅ **Demo/Presentasi** - Tanpa perlu setup kompleks
- ✅ **Pembelajaran** - Contoh aplikasi vanilla JS yang clean
- ✅ **Deployment cepat** - Bisa langsung di-host di static hosting
- ✅ **Offline usage** - Bisa disimpan dan dibuka tanpa internet

## 📄 Lisensi

Aplikasi ini dibuat untuk tujuan pendidikan dan penelitian.

---

**Dibuat dengan ❤️ menggunakan HTML, CSS, dan JavaScript murni**
