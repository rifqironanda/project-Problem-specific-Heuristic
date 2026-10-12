# Replikasi dan batas kesetaraan

Sumber utama: Stopfer & Wagner, arXiv:2509.17876v3, Appendix A/C, equations (3)–(6), sections 2, 5, 6. https://arxiv.org/abs/2509.17876

## Yang sama dan yang berbeda

| Aspek | Paper | Proyek |
|---|---|---|
| Tujuan | MinVola: min wᵀΣw, μᵀw ≥ ε, sum w=1, 0≤w≤u | Sama |
| Return | Daily price ratio, geometric annual return | Sama pada `statistics()` |
| Kovarians | 252/T × centered-return cross product | Sama, ddof=0; tanpa regularisasi |
| Target ε | Quantile 70% asset annual returns | Default sama, user bisa override |
| Batas u | max(0.1,3/n) | Sama; cap 1 untuk domain n<3 |
| Heuristik | n starts, fixed δ=u/2^d, greedy min variance, max-return fallback | Sama prinsip; perbedaan literal/koreksi di bawah |
| Normalisasi | Teks menyatakan scale sum to 1; pseudocode line 50 mengalikan | Mode literal mengalikan; mode corrected membagi |
| Stop loop | Visual pseudocode line 10: sum(x)<1−δ/2 | Sama; ekstraksi PDF salah membaca menjadi 1−2δ |
| QUBO | Varians + 1000(return−(ε+.01))² + 1000(sum−1)² | Sama, full symmetric Q + constant offset |
| Encoding | u[sum_j b_j/2^j + b_(d+1)/2^d] | Sama; koefisien terakhir duplikat, sum koefisien=1 |
| Presisi | d=3 (4 bit/aset) | Notebook menyediakan d=3; app default d=1 untuk demo ringan |
| Dataset | 1.978 NASDAQ assets, 2020–2023; 270 instances/variant | Demo sintetis; fetcher Yahoo dan French alternatif. Tidak mengklaim universe identik |
| Solver | Gurobi optimum diskret; SCIP benchmark kontinu | SLSQP kontinu + enumerasi optimum grid <=16 bit, tanpa Gurobi/SCIP |
| Classical QUBO | Library D-Wave SA/steepest/tabu | Implementasi edukasional NumPy; bukan library/settings identik |
| QAOA | LR, analytic grid p=1, COBYLA initialized LR; p=1..3 | Prinsip circuit sama; grid dievaluasi statevector, bukan formula analytic. Budget iterasi kecil |
| Quantum device | IBM Strasbourg; D-Wave Advantage2 | Simulator ideal; adapter Qiskit/D-Wave opsional, QPU belum dijalankan |
| Fair runtime | 60 s device/train/sampling, overhead tertentu dikecualikan | Demo berdasarkan reads/sweeps/maxiter; timing end-to-end dan training terpisah, bukan benchmark fixed-time yang sama |
| Postprocess | Top 100 QUBO samples, normalize, feasibility check | Sama prinsip; sample multiplicities tidak dihitung pada adapter D-Wave |
| Metric | fm / discrete fopt | `variance_ratio_to_continuous_reference`; tidak disebut approximation ratio paper |
| AI/backtest | Tidak ada | Ekstensi eksplisit, bukan hasil paper |

## Penjelasan heuristik untuk pemula

1. Dana belum dibagi: semua bobot 0. Pilih satu aset awal, beri δ.
2. Coba tambahan δ ke masing-masing aset, satu per satu.
3. Abaikan kandidat yang melewati cap. Hitung return ter-normalisasi agar alokasi parsial bisa dibandingkan dengan target final.
4. Bila ada kandidat memenuhi target, pilih varians terendah. Pada langkah yang sama semua kandidat punya total bobot sama, sehingga penggunaan varians mentah untuk ranking konsisten dengan ranking setelah normalisasi.
5. Bila belum ada yang memenuhi target, pilih return tertinggi untuk mendekati target.
6. Ulangi sampai total alokasi mendekati 1. Normalkan bobot dan cek semua constraint.
7. Ulangi dengan aset awal lainnya. Pilih varians minimum di antara hasil akhir yang layak.

### Mode literal

Mempertahankan finite sentinels +1000/−1000 dan line 50 `x *= sum(x)`. Ini alat audit pseudocode, bukan pilihan default. Normalisasi literal menghasilkan total `(sum x)^2`, bukan 1 kecuali sum x tepat 1. Ia juga bisa menambah aset melampaui cap ketika semua kandidat blocked, seperti argmax placeholder pada pseudocode.

### Mode corrected

`x /= sum(x)`, menggunakan infinity sebagai placeholder agar tidak bergantung skala, menghentikan start jika tak ada kapasitas penambahan, menolak start δ>cap, dan memeriksa hasil akhir. Tidak ada perbaikan tersembunyi jika normalisasi melanggar cap. Hasil gagal tetap dicatat, dan `best=None` bila seluruh start gagal.

Perubahan tersebut adalah interpretasi rekayasa untuk menghasilkan implementasi aman dan dapat ditelusuri, bukan klaim bahwa source code penulis memakai perubahan yang sama. PDF tidak menyediakan source code asli dalam lampiran.

## AI: pembanding dan pelengkap

Fitur: annual geometric return per aset, upper triangle kovarians, batas bobot, target. Target supervised: bobot solver kontinu pada rolling historical windows dengan beberapa quantile target. Identitas/urutan aset harus tetap; model tidak portable ke universe berbeda.

Training: 60% pertama; validasi: 20% berikutnya, pilih kedalaman Random Forest 4 atau 8 berdasarkan MAE bobot. Test: 20% terakhir tidak digunakan untuk fit/tuning/statistik alokasi. Model meniru **solver**, bukan memprediksi return masa depan.

AI comparator: model → proyeksi ke capped simplex (sum=1, bounds) → cek target return. Proyeksi tidak menjamin target return.

AI complement: AI → warm start SLSQP → gabungkan dengan kandidat terbaik heuristic → pilih varians terendah yang layak. Ini melibatkan solver kontinu; bandingkan dengan SLSQP cold start untuk memisahkan kontribusi AI. Jangan mengatribusikan perbaikan ke AI tanpa analisis ablation dan total biaya training.

MAE menunjukkan seberapa dekat bobot AI dengan teacher. Evaluasi test terpisah mencatat realized return, volatility, drawdown. Backtest memakai daily rebalancing dengan bobot statis dan tanpa biaya; bukan kinerja investasi yang dapat langsung diterapkan.

## Cara mendekati benchmark paper penuh

1. Bekukan ticker universe, exact closing-price files 2020–2023, checksum dan versi pengambilan. Ulangi 10 random instances per n dengan seed dan simpan daftar aset.
2. Gunakan d=3, cap dan target paper; cocokkan hasil encoding dan QUBO dengan unit test.
3. Tambahkan Gurobi optimum **diskret dengan constraint asli**; jangan pakai optimum penalty QUBO sebagai pengganti. Bandingkan postprocessing dapat menghasilkan bobot keluar grid, sehingga interpretasi ratio memerlukan kehati-hatian.
4. Gunakan library SA/steepest/tabu dan preset paper; batasi device budget 60 s, catat overhead secara terpisah.
5. Jalankan QPU dengan hardware, transpiler, annealing time, chain strength dan seed yang tercatat. Record calibration/noise, queue, device timing, shots dan chain breaks.
6. Laporkan rata-rata dan standar deviasi 10 instances, feasibility per instance, samples dan biaya. Jangan menyatakan keunggulan kuantum berdasarkan simulator atau hanya satu demo.

Proyek ini tidak menjalankan langkah hardware/berlisensi tersebut secara otomatis.
