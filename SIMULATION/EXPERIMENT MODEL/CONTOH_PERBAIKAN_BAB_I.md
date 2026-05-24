# 📝 CONTOH PERBAIKAN BAB I - PENDAHULUAN

Dibuat: 22 Januari 2026  
Dokumen ini berisi contoh konkret revisi Bab I berdasarkan feedback sempro

---

## 📌 BAGIAN 1.1 - LATAR BELAKANG

### ✏️ PERBAIKAN 1: Paragraf 1 - Kurangi Fokus "Pengelolaan"

#### ❌ SEBELUM (Versi Lama):
```
Dengan demikian, pengelolaan pariwisata yang tepat guna tidak hanya 
memanjakan wisatawan, tetapi juga menjadi fondasi kesejahteraan (well-being) 
dan stabilitas ekonomi bagi penduduk setempat (Godovykh et al., 2025).
```

#### ✅ SESUDAH (Versi Perbaikan):
```
Dengan demikian, aktivitas wisata tidak hanya berdampak pada pemulihan mental 
wisatawan, tetapi juga memberikan kontribusi ekonomi riil bagi penduduk 
setempat melalui interaksi langsung dengan UMKM lokal dan sektor jasa 
pariwisata (Godovykh et al., 2025). Namun, untuk memaksimalkan manfaat 
tersebut, wisatawan membutuhkan alat bantu yang memudahkan perencanaan 
perjalanan—khususnya dalam mengelola anggaran biaya secara efektif.
```

**💡 ALASAN PERUBAHAN:**
- ❌ Hapus fokus pada "pengelolaan pariwisata" (bukan masalah utama user)
- ✅ Fokus pada perspektif wisatawan (user-centric)
- ✅ Membuka jembatan ke masalah: butuh alat bantu perencanaan

---

### ✏️ PERBAIKAN 2: Paragraf 2 - Tambahkan Penjelasan "Malang Raya"

#### ❌ SEBELUM (Versi Lama):
```
Kawasan Malang Raya di Jawa Timur kini telah menjelma menjadi magnet wisata 
yang menarik perhatian domestik maupun mancanegara. Meningkatnya minat wisata 
terlihat jelas dari jumlah kunjungan wisatawan pada tahun 2024, yang mencapai 
949.681 orang pada Oktober 2025 (BPS Kota Malang, 2025).

[Langsung lanjut ke paragraf berikutnya tentang jumlah destinasi]
```

#### ✅ SESUDAH (Versi Perbaikan):
```
Kawasan Malang Raya di Jawa Timur kini telah menjelma menjadi magnet wisata 
yang menarik perhatian domestik maupun mancanegara. Meningkatnya minat wisata 
terlihat jelas dari jumlah kunjungan wisatawan pada tahun 2024, yang mencapai 
949.681 orang pada Oktober 2025 (BPS Kota Malang, 2025). Wilayah Malang Raya, 
yang meliputi Kota Malang, Kabupaten Malang, dan Kota Batu, memiliki kekayaan 
objek wisata yang beragam dan dapat diandalkan sebagai destinasi pariwisata 
unggulan dengan peluang pengembangan yang besar di masa mendatang (Utama et al., 
2024). Keragaman daya tarik wisata di kawasan ini mencakup wisata alam, budaya, 
sejarah, belanja, dan wisata buatan, dengan jarak tempuh antar wilayah yang 
relatif dekat sehingga memungkinkan wisatawan menyusun paket perjalanan 
multi-destinasi dalam satu trip.

[Dilanjutkan paragraf berikutnya]
```

**💡 ALASAN PERUBAHAN:**
- ✅ Menjelaskan **kenapa Malang Raya**, bukan hanya Kota Malang
- ✅ Memperkuat justifikasi objek penelitian dengan data dari jurnal
- ✅ Menjelaskan keragaman wisata: alam, budaya, sejarah, belanja, wisata buatan
- ✅ Menggunakan referensi yang akurat dari jurnal `malangraya.pdf`

**📚 REFERENSI LENGKAP:**
```
Utama, A., Sabilla, W. I., & Wakhidah, R. (2024). Sistem Rekomendasi Tempat 
Wisata di Malang Raya Menggunakan Algoritma K-Means Clustering dan Simple 
Additive Weighting (SAW). Jurnal Informatika & Multimedia, 16(1).
```

---

### ✏️ PERBAIKAN 3: Tambahkan Paragraf Baru - Target User (Wisatawan Individual)

#### ❌ SEBELUM (Versi Lama):
```
[Paragraf tentang budget constraint]
...sehingga keputusan yang diambil tidak selalu optimal terhadap batasan 
anggaran (Rahmanita, 2025).

[Langsung lanjut ke paragraf tentang FCM]
Dalam konteks ini, algoritma Fuzzy C-Means (FCM)...
```

#### ✅ SESUDAH (Versi Perbaikan):
```
[Paragraf tentang budget constraint]
...sehingga keputusan yang diambil tidak selalu optimal terhadap batasan 
anggaran (Rahmanita, 2025).

Masalah ini terutama dirasakan oleh wisatawan individual (independent travelers) 
yang merencanakan perjalanan secara mandiri tanpa bantuan travel agent. Berbeda 
dengan paket wisata terorganisir, wisatawan individual harus menyusun sendiri 
itinerary, memilih akomodasi, tempat makan, dan objek wisata yang sesuai dengan 
anggaran mereka. Tanpa alat bantu yang tepat, proses perencanaan ini tidak hanya 
memakan waktu, tetapi juga rentan terhadap kesalahan estimasi biaya yang dapat 
mengganggu kenyamanan perjalanan (Sutjiadi et al., 2018).

[Lanjut ke paragraf FCM]
```

**💡 ALASAN PERUBAHAN:**
- ✅ **Eksplisit menyebutkan target user:** wisatawan individual
- ✅ Membedakan dengan travel agent (sistem bukan untuk mereka)
- ✅ Memperkuat urgensi sistem
- ✅ Menjawab feedback: "User tidak disebutkan pada latar belakang"

---

### ✏️ PERBAIKAN 4: Paragraf FCM - Perjelas "FCM untuk Clustering Apa?"

#### ❌ SEBELUM (Versi Lama):
```
Dalam konteks ini, algoritma Fuzzy C-Means (FCM) diterapkan karena 
kemampuannya memetakan data dengan logika samar (fuzzy). FCM memungkinkan 
suatu objek dimiliki oleh lebih dari satu cluster dengan tingkat keanggotaan 
yang berbeda-beda (Wardani et al., 2023).
```

#### ✅ SESUDAH (Versi Perbaikan):
```
Dalam konteks ini, algoritma Fuzzy C-Means (FCM) diterapkan untuk 
mengelompokkan paket wisata berdasarkan profil penganggaran biaya (budget 
breakdown) yang mencakup tiga komponen utama: harga tiket wisata, akomodasi 
(hotel), dan kuliner. Kemampuan FCM dalam memetakan data dengan logika samar 
(fuzzy) memungkinkan sistem untuk menangani variasi harga yang tidak tegas—
misalnya, sebuah paket bisa memiliki keanggotaan parsial pada kategori 'Budget 
Sedang' dan 'Budget Tinggi' sekaligus, sehingga memberikan fleksibilitas 
rekomendasi yang lebih presisi (Wardani et al., 2023).
```

**💡 ALASAN PERUBAHAN:**
- ✅ **Menjawab langsung:** FCM untuk clustering paket wisata berdasarkan budget
- ✅ Menjelaskan kenapa fuzzy logic penting untuk kasus ini
- ✅ Memberikan contoh konkret: keanggotaan parsial
- ✅ Menjawab feedback: "FCM untuk clustering apa?"

---

### ✏️ PERBAIKAN 5: Tambahkan Paragraf - Urgensi Paket Wisata

#### ❌ SEBELUM (Versi Lama):
```
[Paragraf tentang information overload]
...wisatawan mengalami information overload dan kesulitan menentukan 
prioritas biaya (Rahmanita, 2025).

[Langsung lanjut ke paragraf tentang wisatawan individual]
```

#### ✅ SESUDAH (Versi Perbaikan):
```
[Paragraf tentang information overload]
...wisatawan mengalami information overload dan kesulitan menentukan 
prioritas biaya (Rahmanita, 2025).

Dalam konteks ini, konsep 'paket wisata' menjadi solusi yang relevan karena 
memungkinkan wisatawan untuk mendapatkan estimasi biaya secara komprehensif—
mencakup akomodasi, destinasi, dan kuliner—dalam satu bundel informasi yang 
terstruktur. Berbeda dengan pencarian manual yang terpisah-pisah, paket wisata 
memberikan gambaran total pengeluaran (total cost) secara transparan, sehingga 
memudahkan wisatawan dalam mengambil keputusan yang sesuai dengan kapasitas 
finansial mereka (Sutjiadi et al., 2018). Namun, tantangan utamanya adalah 
bagaimana menyusun paket-paket tersebut agar dapat disesuaikan secara dinamis 
dengan preferensi budget setiap wisatawan.

[Lanjut ke paragraf wisatawan individual]
```

**💡 ALASAN PERUBAHAN:**
- ✅ Menjelaskan **kenapa paket wisata** (bukan item terpisah)
- ✅ Menjawab urgensi: efisiensi + transparansi biaya
- ✅ Menjawab feedback Pak Alifian: "Urgensi Paket Wisata"

---

## 📌 BAGIAN 1.2 - RUMUSAN MASALAH

### ✏️ PERBAIKAN 6: Tambahkan Poin Evaluasi

#### ❌ SEBELUM (Versi Lama):
```
Berdasarkan latar belakang di atas, maka dapat dirumuskan masalah 
sebagai berikut:

1. Bagaimana mengimplementasikan algoritma Fuzzy C-Means (FCM) untuk 
   mengklasifikasikan paket wisata berdasarkan profil penganggaran 
   (budget breakdown) di kawasan Malang Raya?

2. Bagaimana membangun sistem rekomendasi paket wisata berbasis web 
   yang dapat memberikan saran paket sesuai dengan batasan anggaran 
   (budget constraint) pengguna?
```

#### ✅ SESUDAH (Versi Perbaikan):
```
Berdasarkan latar belakang di atas, maka dapat dirumuskan masalah 
sebagai berikut:

1. Bagaimana mengimplementasikan algoritma Fuzzy C-Means (FCM) untuk 
   mengklasifikasikan paket wisata berdasarkan profil penganggaran 
   (budget breakdown) di kawasan Malang Raya?

2. Bagaimana membangun sistem rekomendasi paket wisata berbasis web 
   yang dapat memberikan saran paket sesuai dengan batasan anggaran 
   (budget constraint) pengguna?

3. Bagaimana mengevaluasi kinerja sistem rekomendasi paket wisata 
   berbasis algoritma Fuzzy C-Means (FCM) dalam hal akurasi clustering 
   dan kepuasan pengguna (user satisfaction)?
```

**💡 ALASAN PERUBAHAN:**
- ✅ Setiap sistem perlu evaluasi
- ✅ Menunjukkan penelitian lengkap (implementasi + evaluasi)
- ✅ Menjawab feedback Bu Tesa: "Tambahkan poin 3: Bagaimana mengevaluasi?"

---

## 📌 BAGIAN 1.3 - TUJUAN PENELITIAN

### ✏️ PERBAIKAN 7: Tambahkan Tujuan Evaluasi

#### ❌ SEBELUM (Versi Lama):
```
Berdasarkan rumusan masalah di atas, maka dapat diketahui tujuan dari 
penelitian ini yaitu:

1. Menerapkan algoritma Fuzzy C-Means (FCM) untuk mengklasifikasikan 
   paket wisata berdasarkan profil penganggaran biaya (budget breakdown) 
   di kawasan Malang Raya.

2. Membangun aplikasi sistem rekomendasi paket wisata berbasis web yang 
   mampu memberikan rekomendasi paket wisata sesuai dengan batasan 
   anggaran pengguna.
```

#### ✅ SESUDAH (Versi Perbaikan):
```
Berdasarkan rumusan masalah di atas, maka dapat diketahui tujuan dari 
penelitian ini yaitu:

1. Menerapkan algoritma Fuzzy C-Means (FCM) untuk mengklasifikasikan 
   paket wisata berdasarkan profil penganggaran biaya (budget breakdown) 
   di kawasan Malang Raya.

2. Membangun aplikasi sistem rekomendasi paket wisata berbasis web yang 
   mampu memberikan rekomendasi paket wisata sesuai dengan batasan 
   anggaran pengguna.

3. Mengevaluasi kinerja sistem rekomendasi paket wisata berbasis 
   algoritma Fuzzy C-Means (FCM) menggunakan metrik validitas kluster 
   (Silhouette Coefficient dan Davies-Bouldin Index) serta pengujian 
   kepuasan pengguna (System Usability Scale - SUS), untuk memastikan 
   sistem menghasilkan rekomendasi yang akurat dan memenuhi kebutuhan 
   wisatawan.
```

**💡 ALASAN PERUBAHAN:**
- ✅ Simetri dengan rumusan masalah
- ✅ Menunjukkan metode evaluasi yang jelas (teknis + user satisfaction)
- ✅ Menjawab feedback: "Harusnya juga ditambahkan di tujuan"

---

## 📌 BAGIAN 1.5 - BATASAN MASALAH

### ✏️ PERBAIKAN 8: Detail "Kriteria-Kriteria Tertentu"

#### ❌ SEBELUM (Versi Lama):
```
1. Penelitian ini hanya mempertimbangkan kriteria-kriteria tertentu dalam 
   penentuan rekomendasi paket pariwisata yang akan diolah oleh sistem. 
   Kriteria tersebut mencakup kategori wisata, estimasi harga, lokasi 
   koordinat geografis untuk paket hotel, tempat wisata, dan tempat makan.
```

#### ✅ SESUDAH (Versi Perbaikan):
```
1. Penelitian ini hanya mempertimbangkan kriteria-kriteria berikut dalam 
   penentuan rekomendasi paket pariwisata yang akan diolah oleh sistem:
   
   a. Kategori wisata (wisata alam, budaya, kuliner, dll)
   b. Estimasi harga tiket masuk objek wisata
   c. Estimasi harga akomodasi (hotel/penginapan)
   d. Estimasi harga kuliner (tempat makan)
   e. Lokasi geografis (koordinat latitude/longitude)
   f. Rating/ulasan pengguna (dari Google Maps)
   
   Variabel yang digunakan sebagai input utama algoritma Fuzzy C-Means 
   (FCM) adalah proporsi penganggaran biaya (budget breakdown) yang 
   mencakup tiga komponen: harga tiket wisata, akomodasi, dan kuliner.
```

**💡 ALASAN PERUBAHAN:**
- ✅ **Spesifik menyebutkan kriteria**, bukan hanya "tertentu"
- ✅ Membedakan antara kriteria umum vs kriteria FCM
- ✅ Menjawab feedback: "Sebutkan kriterianya, jangan hanya 'tertentu'"

---

### ✏️ PERBAIKAN 9: Detail Sumber Data

#### ❌ SEBELUM (Versi Lama):
```
2. Data sekunder terkait objek wisata, tempat makan, dan akomodasi di 
   Kota Malang diperoleh melalui teknik Automated Web Scraping terhadap 
   platform Google Maps, yang merupakan sumber informasi paling dominan 
   diakses oleh wisatawan dalam tahap perencanaan perjalanan 
   (Kumar, 2023).
```

#### ✅ SESUDAH (Versi Perbaikan):
```
2. Data sekunder terkait objek wisata, tempat makan, dan akomodasi di 
   kawasan Malang Raya (Kota Malang, Kabupaten Malang, dan Kota Batu) 
   diperoleh melalui teknik Automated Web Scraping terhadap platform 
   Google Maps, yang merupakan sumber informasi paling dominan diakses 
   oleh wisatawan dalam tahap perencanaan perjalanan (Kumar, 2023). 
   Data mencakup wilayah Malang Raya dengan kata kunci pencarian 
   spesifik: 'tempat wisata', 'hotel', dan 'tempat makan' yang 
   dilakukan pada periode Januari 2026. Proses scraping dilakukan dengan 
   metode browser automation untuk menangani konten dinamis 
   (lazy loading) pada Google Maps.
```

**💡 ALASAN PERUBAHAN:**
- ✅ Ganti "Kota Malang" → "**Malang Raya**" (konsisten!)
- ✅ Detail waktu pengambilan data
- ✅ Detail kata kunci scraping
- ✅ Detail metode teknis (browser automation)
- ✅ Menjawab feedback: "Pendetilan data dan sumber yang dipakai"

---

## 📊 CHECKLIST PERBAIKAN (Yang Sudah Dicontohkan)

### ✅ LATAR BELAKANG (1.1)
- [x] ✅ Perbaikan 1: Kurangi fokus "pengelolaan" → user-centric
- [x] ✅ Perbaikan 2: Tambah penjelasan "Malang Raya" (3 wilayah)
- [x] ✅ Perbaikan 3: Tambah paragraf target user (wisatawan individual)
- [x] ✅ Perbaikan 4: Perjelas "FCM untuk clustering paket wisata berdasarkan budget"
- [x] ✅ Perbaikan 5: Tambah urgensi paket wisata

### ✅ RUMUSAN MASALAH (1.2)
- [x] ✅ Perbaikan 6: Tambah poin 3 tentang evaluasi

### ✅ TUJUAN PENELITIAN (1.3)
- [x] ✅ Perbaikan 7: Tambah poin 3 tentang evaluasi dengan metrik

### ✅ BATASAN MASALAH (1.5)
- [x] ✅ Perbaikan 8: Detail "kriteria-kriteria tertentu" → spesifik
- [x] ✅ Perbaikan 9: Detail sumber data (Malang Raya, waktu, metode)

---

## 🎯 CARA MENGGUNAKAN CONTOH INI

### Langkah 1: Baca Contoh Perbaikan di Atas
Pahami **MENGAPA** setiap perubahan dilakukan, bukan hanya **APA** yang diubah.

### Langkah 2: Buka Bab 1 Skripsi Anda
Cari bagian yang sesuai dengan contoh perbaikan.

### Langkah 3: Terapkan Perbaikan
Salin versi "SESUDAH" dan sesuaikan dengan konteks kalimat Anda.

### Langkah 4: Review Konsistensi
Pastikan:
- ✅ Semua "Kota Malang" → "Malang Raya"
- ✅ Fokus user-centric (bukan pengelolaan)
- ✅ Target user disebutkan eksplisit (wisatawan individual)

---

## 💡 TIPS PENTING

### 1. Jangan Copas Mentah-mentah
Sesuaikan dengan kalimat Anda yang sudah ada. Ini **template**, bukan pengganti total.

### 2. Perhatikan Referensi
- Baca `malang raya.pdf` untuk referensi Malang Raya
- Pastikan referensi yang dikutip sesuai

### 3. Konsistensi Bahasa
- Gunakan "**wisatawan individual**" atau "**independent travelers**" konsisten
- Gunakan "**Malang Raya**" konsisten (bukan kadang Kota Malang)

### 4. Review Feedback Dosen
Setiap perbaikan di atas menjawab **feedback spesifik** dari dosen:
- ✅ Bu Tesa: User tidak disebutkan, pengelolaan tidak relevan
- ✅ Pak Alifian: Urgensi paket wisata, detail kriteria
- ✅ Umum: FCM untuk clustering apa, evaluasi sistem

---

## 📚 REFERENSI YANG PERLU DITAMBAHKAN

Untuk tambahan paragraf Malang Raya (Perbaikan 2), gunakan referensi berikut:

```
Utama, A., Sabilla, W. I., & Wakhidah, R. (2024). Sistem Rekomendasi Tempat 
Wisata di Malang Raya Menggunakan Algoritma K-Means Clustering dan Simple 
Additive Weighting (SAW). Jurnal Informatika & Multimedia, 16(1), 1-11.
ISSN: 2252-486X (print), 2548-4710 (electronic).
```

**📝 INFORMASI KUNCI DARI JURNAL:**
- ✅ **Definisi Malang Raya:** Kota Malang, Kabupaten Malang, dan Kota Batu
- ✅ **Keragaman Wisata:** Alam, budaya, sejarah, belanja, dan wisata buatan
- ✅ **Julukan Kota Malang:** Paris van Oost Java (Parisnya Jawa Timur), kota bunga, 
                          kota pendidikan, kota sejarah, kota wisata, kota apel, 
                          kota dingin, bumi arema
- ✅ **Justifikasi:** Kekayaan objek wisata dapat diandalkan dengan peluang 
                     pengembangan besar di masa depan

---

## 🎓 KESIMPULAN

Dokumen ini memberikan **9 contoh konkret perbaikan** untuk Bab 1 berdasarkan feedback sempro.

**POIN UTAMA PERBAIKAN:**
1. ✅ User-centric (fokus wisatawan, bukan pengelolaan)
2. ✅ Malang Raya (3 wilayah terintegrasi)
3. ✅ Target user eksplisit (wisatawan individual)
4. ✅ FCM untuk clustering paket berdasarkan budget
5. ✅ Tambah evaluasi sistem (Silhouette, DBI, SUS)
6. ✅ Detail kriteria (bukan "tertentu")
7. ✅ Detail sumber data (waktu, metode, cakupan)

---

**SEMANGAT REVISI! 💪**

Jika ada bagian yang masih bingung atau butuh penjelasan lebih lanjut, tanyakan saja! 😊
