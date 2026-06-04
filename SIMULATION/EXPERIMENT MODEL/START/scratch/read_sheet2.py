import pandas as pd

filename = "/Users/macbookpro/Documents/GITHUB/PROJET-SKRIPSI/SIMULATION/EXPERIMENT MODEL/START/rekomendasi_paket.xlsx"
xl = pd.ExcelFile(filename)
df2 = xl.parse("Rincian Per Opsi")

# Set display options to show everything
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)

print(df2.iloc[:, :5])
