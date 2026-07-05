"""
Olah / standarisasi kategori mentah hasil scraping menjadi Meta-Kategori + Nilai Numerik
untuk 3 dataset: HOTEL, WISATA, KULINER (folder "data new").

Prinsip:
- Kolom `Kategori` mentah didominasi noise ("Wisata Umum", nama tempat, koordinat),
  jadi klasifikasi memakai keyword pada gabungan (Nama_Tempat + " " + Kategori).lower().
- Keyword dicek BERURUTAN (spesifik/premium dulu) -> match pertama menang.
- Baris yang tidak cocok apa pun -> Meta_Kategori="Unknown", Nilai_Numerik=-1 (untuk review manual).

Output: file *_kategori.xlsx per dataset + ringkasan jumlah per kelas di terminal.
"""

import os
import re
import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data new")

# ----------------------------------------------------------------------------
# Aturan klasifikasi.
# Tiap dataset = list of (nilai_numerik, nama_meta_kategori, pola_regex).
# DICEK BERURUTAN dari atas ke bawah -> yang pertama cocok dipakai.
# Taruh yang paling spesifik / prioritas tertinggi di ATAS.
# ----------------------------------------------------------------------------

RULES = {
    # Catatan: Nilai_Numerik tetap 3 tier (0/1/2) sebagai input FCM, tapi label
    # Meta_Kategori dibuat rinci sesuai kategori MURNI scraping (per bintang).
    # Kategori bintang dari scraping diprioritaskan (dicek paling atas), lalu
    # Resort/Villa & Penginapan, terakhir "Hotel" (tanpa keterangan bintang).
    "HOTEL": [
        # --- kategori bintang murni (prioritas tertinggi) ---
        (2, "Hotel Bintang 5", r"bintang 5"),
        (2, "Hotel Bintang 4", r"bintang 4"),
        (1, "Hotel Bintang 3", r"bintang 3"),
        (1, "Hotel Bintang 2", r"bintang 2"),
        (1, "Hotel Bintang 1", r"bintang 1"),
        # --- tier 2: resort/villa/glamping (tanpa keterangan bintang) ---
        (2, "Resort / Villa",
         r"resort|resor|\bvilla|glamping|glamp|cabin|cottage|luxury|boutique|heritage hotel|convention"),
        # --- tier 0: penginapan/homestay ---
        (0, "Penginapan / Homestay",
         r"homestay|home ?stay|guest ?house|hostel|\bkos\b|\bkost\b|wisma|penginapan|pondok|"
         r"rumah wisata|backpacker|\bmotel\b|b&b|kapsul|\boyo\b|reddoorz|sewa kamar|losmen|"
         r"residence|\bomah\b|\bhouse\b|joglo|millennial|graha"),
        # --- tier 1: hotel tanpa keterangan bintang = "Hotel" ---
        (1, "Hotel",
         r"business hotel|\binn\b|hotel jangka panjang|bujet simpel|favehotel|amaris|\bhotel\b"),
        # --- fallback (recover agresif): sisa -> kelas mayoritas Penginapan/Homestay ---
        (0, "Penginapan / Homestay", r".*"),
    ],

    "WISATA": [
        # 2 = Rekreasi Modern (dicek sebelum "taman" polos & sebelum alam)
        (2, "Wisata Rekreasi Modern",
         r"theme park|jatim park|museum angkut|waterpark|kolam renang|taman rekreasi|taman hiburan|"
         r"wahana|playground|taman bermain|kebun binatang|\bzoo\b|secret zoo|\bbns\b|selecta|sengkaling|"
         r"dreamland|predator|eco green|alun.?alun|night spectacular|flower garden|glow garden|"
         r"lampion|santerra|adventure|edupark|\bsport|extreme|skyland|jungle|green farm|selfie|payung"),
        # 1 = Budaya & Edukasi (termasuk Religi)
        (1, "Wisata Budaya & Edukasi",
         r"museum|candi|keraton|monumen|situs|galeri|masjid|wisata religi|\bmakam\b|petilasan|"
         r"desa wisata|kampung|kampoeng|kampung warna|edukasi|krida budaya|klenteng|vihara|gereja|"
         r"heritage|pasar wisata|desa \w*wisata|pecinan|\bpura\b|kwan im|topeng|kayutangan|boulevard|"
         r"holland|budaya"),
        # 0 = Wisata Alam (termasuk agrowisata, sungai, goa, & "taman" polos)
        (0, "Wisata Alam",
         r"pantai|gunung|bukit|coban|air terjun|waterfall|curug|sumber|umbulan|hutan|kebun|pemandian|"
         r"danau|telaga|embung|bendungan|waduk|reservoir|agrowisata|\bagro\b|petik|apel|jeruk|"
         r"stroberi|strawberr|buah|sawah|wana wisata|paralayang|savana|savanna|hill|hot spring|"
         r"\bgua\b|\bgoa\b|watu|teluk|rowo|rafting|arung jeram|pemancingan|pancing|fishing|\bkali\b|\bpark\b|"
         r"outbound|camp|kemah|puncak|lembah|jembatan|bridge|pulau|tebing|geo|dusun|nanas|cangar|\btaman\b"),
        # fallback (recover agresif): sisa -> kelas mayoritas Wisata Alam
        (0, "Wisata Alam", r".*"),
    ],

    "KULINER": [
        # 2 = Restoran
        (2, "Restoran",
         r"restoran|\bresto\b|restaurant|rumah makan|\brm\b|\brm\.|fine dining|buffet|seafood|steak|"
         r"steakhouse|prasmanan|kitchen|dapoer|cuisine|joglo|gubug makan|gubuk|rumah santai|catering"),
        # 1 = Cafe & Coffee Shop  (dicek sebelum "warung" utk nama hybrid spt "Cafe & Warung")
        (1, "Cafe & Coffee Shop",
         r"cafe|kafe|coffee|koffie|coffie|\bkopi\b|kedai kopi|bistro|diner|bakery|pastry|gelato|"
         r"eater|lounge|skylounge|\bbar\b"),
        # 0 = Warung / Kuliner Lokal
        (0, "Warung / Kuliner Lokal",
         r"warung|waroeng|angkringan|kaki lima|depot|lesehan|bakso|soto|pecel|rujak|sate|lalapan|ceker|"
         r"\bnasi\b|nasgor|sego|rawon|bebek|\bayam\b|\btahu\b|tempe|dimsum|mie|\bmi\b|bakmi|gule|"
         r"gulai|\biga\b|pangsit|geprek|penyet|pentol|gado|kuliner|dapur|pawon|jajan|onde|kedai|"
         r"bakar|\bsop\b|\bsup\b|kikil|gudeg|kambing|gurami|menthok|lodeh|orem|kupang|ketan|roti|"
         r"stmj|warteg|warmindo|masakan|padang|ampera|iwak|makan|dahar|pinarak|madhang|sambel|"
         r"sambal|betutu|tempong|chicken|gudla|lauk|cobek|lontong|sekuteng|ketan"),
        # fallback (recover agresif): sisa -> kelas mayoritas Warung / Kuliner Lokal
        (0, "Warung / Kuliner Lokal", r".*"),
    ],
}

# Peta nama file -> jenis dataset
FILES = {
    "hotelv2.xlsx": "HOTEL",
    "wisataV2.xlsx": "WISATA",
    "tempat_makanV2.xlsx": "KULINER",
}


def classify(text: str, rules) -> tuple:
    """Kembalikan (nilai_numerik, meta_kategori, sumber_label) untuk satu baris teks.
    sumber_label = 'keyword' bila cocok aturan keyword, 'default' bila kena fallback (r'.*')."""
    t = str(text).lower()
    for nilai, meta, pola in rules:
        if re.search(pola, t):
            sumber = "default" if pola == r".*" else "keyword"
            return nilai, meta, sumber
    return -1, "Unknown", "none"


def process_file(fname: str, jenis: str):
    path = os.path.join(BASE_DIR, fname)
    df = pd.read_excel(path)

    # Sumber teks = Nama_Tempat + Kategori
    src = (df["Nama_Tempat"].astype(str) + " " + df["Kategori"].astype(str))
    rules = RULES[jenis]
    hasil = src.apply(lambda s: classify(s, rules))
    df["Nilai_Numerik"] = hasil.apply(lambda x: x[0])
    df["Meta_Kategori"] = hasil.apply(lambda x: x[1])
    df["Sumber_Label"] = hasil.apply(lambda x: x[2])

    out = os.path.join(BASE_DIR, fname.replace(".xlsx", "_kategori.xlsx"))
    df.to_excel(out, index=False)

    # Ringkasan
    total = len(df)
    print(f"\n{'='*60}\n{jenis}  ({fname})  total={total}")
    vc = df["Meta_Kategori"].value_counts()
    for meta, n in vc.items():
        nilai = df.loc[df["Meta_Kategori"] == meta, "Nilai_Numerik"].iloc[0]
        print(f"  [{nilai:>2}] {meta:<28} {n:>4}  ({n/total*100:5.1f}%)")
    default = (df["Sumber_Label"] == "default").sum()
    print(f"  --> semua {total} baris terklasifikasi | via keyword: {total-default}"
          f" | via fallback/default (tebakan): {default} ({default/total*100:.1f}%)")
    print(f"  disimpan: {out}")

    # Tampilkan contoh baris yang kena fallback (tebakan) untuk transparansi
    if default:
        contoh = df.loc[df["Sumber_Label"] == "default", ["Nama_Tempat", "Kategori"]].head(10)
        print("  contoh baris via fallback/default:")
        for _, r in contoh.iterrows():
            print(f"     - {r['Nama_Tempat']}  |  {r['Kategori']}")


def main():
    for fname, jenis in FILES.items():
        process_file(fname, jenis)


if __name__ == "__main__":
    main()
