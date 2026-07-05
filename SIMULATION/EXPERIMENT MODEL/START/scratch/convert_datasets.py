import pandas as pd
import os

files = ["hotel_clean", "wisata_clean", "tempat_makan_clean"]
base_dir = "/Users/prom4/Documents/GITHUB/PROJET-SKRIPSI/SIMULATION/EXPERIMENT MODEL/START"

for file in files:
    xlsx_path = os.path.join(base_dir, f"{file}.xlsx")
    csv_path = os.path.join(base_dir, f"{file}.csv")
    if os.path.exists(xlsx_path):
        df = pd.read_excel(xlsx_path)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"Successfully converted {xlsx_path} to {csv_path} ({len(df)} rows)")
    else:
        print(f"Error: {xlsx_path} not found")
