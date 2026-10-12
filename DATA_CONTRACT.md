# Kontrak data

Format wide CSV UTF-8, kolom `date` wajib, kolom lain nama aset unik. Satu baris per hari; minimal 80 hari untuk algoritma, disarankan >=600 hari agar training/validation AI memadai. API membatasi 12 aset, 3.000 hari dan 5 MB. Notebook dapat mengolah lebih banyak aset, tetapi QAOA maksimal 14 bit dan exact enumeration maksimal 16 bit.

```csv
date,AAPL,MSFT,AMZN
2020-01-02,0.012,-0.003,0.008
2020-01-03,-0.004,0.006,0.002
```

- `kind=returns`: daily simple return desimal. Nilai 0.01 adalah 1%, bukan 0.01%.
- `kind=prices`: harga penutupan positif; pilih raw/adjusted close secara konsisten dan rekam sumber. Backend menghitung `price[t]/price[t-1]-1` tanpa mengisi missing values.
- Tanggal valid, unik; input diurutkan berdasarkan tanggal. Tidak perlu mengisi weekend/libur; tidak diasumsikan setiap kalender hari adalah trading day.
- Semua angka finite, tidak kosong; return > -1. Missing data ditolak, bukan diam-diam diinterpolasi. Untuk reproduksi paper, pilih aset lengkap pada periode 2020–2023 dan laporkan bias survivorship/universe.
- Dataset alternatif French sudah berupa return; jangan menghitung pct_change sekali lagi.
- Return tahunan paper adalah geometric annualization; kovarians population `ddof=0`, dikali 252. Satuan target return tahunan juga desimal.
- Header nama aset bukan label kelas. AI proyek ini memprediksi **bobot alokasi**, bukan supervised klasifikasi.

Database menggunakan bentuk long: `(dataset_id, date, asset, value)`, primary key gabungan mencegah duplikasi pada dataset yang sama. SHA-256 merekam data yang dipakai eksperimen.
