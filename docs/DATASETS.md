# Rekomendasi dataset gratis

## 1. Kenneth French — 30 Industry Portfolios Daily (disarankan untuk belajar)

Halaman resmi: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
ZIP CSV: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_Daily_CSV.zip

Data publik dapat diunduh tanpa API key. Berisi return harian portofolio industri AS; 30 portofolio ini diperlakukan sebagai aset untuk latihan. Ini **bukan** 30 saham NASDAQ dan bukan dataset asli paper. Sumber menyediakan value-weighted dan equal-weighted blocks; fetcher hanya membaca block pertama (value weighted). Return persen dibagi 100. Missing sentinels −99.99/−999 diubah menjadi missing; kolom tidak lengkap pada rentang dipilih dihapus dan universe akhir tercatat.

```powershell
.\.venv\Scripts\python.exe -m scripts.download_data --source french --start 2020-01-01 --end 2024-01-01
```

Jika unduhan otomatis diblokir, unduh ZIP via browser lalu:

```powershell
.\.venv\Scripts\python.exe -m scripts.download_data --source french --zip "C:\Downloads\30_Industry_Portfolios_Daily_CSV.zip"
```

Gunakan seluruh 30 aset di notebook untuk heuristik klasik. Untuk API pilih maksimum 12 aset; untuk QAOA d=3 pilih 3 aset agar 12 qubit. Ketersediaan gratis tidak berarti lisensi bebas redistribusi; simpan sumber dan jangan memasukkan dataset pihak ketiga ke repo tanpa memeriksa hak penggunaan. Seri resmi dapat direvisi, jadi arsipkan file mentah dan checksum untuk reproduksibilitas.

## 2. Yahoo Finance melalui yfinance — paling dekat dengan sumber paper

Dokumentasi: https://ranaroussi.github.io/yfinance/
Paper memakai historical NASDAQ closing prices melalui yfinance pada 2020–2023. Mulai dari AAPL, MSFT, AMZN, GOOGL, META, NVDA. Pilihan ini adalah universe kecil untuk latihan; bukan reproduksi universe 1.978 saham atau hasil penulis.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[market]"
.\.venv\Scripts\python.exe -m scripts.download_data --source yahoo --start 2020-01-01 --end 2024-01-01 --tickers AAPL,MSFT,AMZN,GOOGL,META,NVDA
```

Pengambilan publik umumnya tidak memakai API berbayar, tetapi dapat mengalami rate limit atau perubahan layanan. yfinance menyebut data Yahoo untuk penggunaan personal dan tool untuk research/education. Untuk aplikasi publik/komersial, periksa terms dan lisensi. Fetcher memakai `auto_adjust=False`, kolom Close sesuai deskripsi paper; split/dividend adjustment tidak diterapkan diam-diam. Data tidak lengkap dikeluarkan.

## 3. Dataset sintetis bawaan — paling reproducible/offline

`data/demo_returns.csv`: enam aset, 756 business-day observations, faktor bersama dan noise, seed 42. Gratis sebagai bagian kode proyek. Cocok untuk unit test, debugging API/database, notebook tanpa jaringan. **Tidak bisa digunakan sebagai bukti profitabilitas atau kesimpulan industri.**

Untuk semua sumber: metadata harus merekam periode, universe, satuan, corporate-action adjustment, checksum, waktu pengambilan, dan sumber. Tidak mengisi missing data memakai informasi masa depan.
