# project-Problem-specific-Heuristic

Laboratorium reproduksi **MinVola** dari Eric Stopfer & Friedrich Wagner, *Quantum Portfolio Optimization: An Extensive Benchmark*, arXiv:2509.17876v3 (7 Oktober 2026). https://arxiv.org/abs/2509.17876

Tujuan: memahami alokasi dana ke aset, mereplikasi prinsip heuristik khusus masalah, membandingkan algoritma klasik/kuantum simulator, dan menambahkan AI melalui aplikasi Python yang dapat dijalankan ulang.

**Cakupan kejujuran eksperimen:** ini reproduksi prinsip dan formulasi, bukan salinan hasil benchmark paper. Tidak ada akses ke dataset 1.978 saham asli, Gurobi berlisensi, IBM Strasbourg atau D-Wave Advantage2 dalam pengujian lokal. Perbedaan lengkap ada di `docs/REPLICATION.md`. Hasil kuantum lokal adalah simulasi klasik ideal, bukan bukti quantum advantage.

## Mulai di Windows + VS Code

1. Ekstrak proyek dan buka folder ini melalui VS Code. Pasang Python 3.12, Git, ekstensi Python dan Jupyter. Docker Desktop diperlukan untuk PostgreSQL/container.
2. Buka terminal PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
Copy-Item .env.example .env
```

3. Untuk percobaan pertama tanpa Docker, ubah `.env`:

```dotenv
DATABASE_URL=sqlite:///./psh.db
API_BASE_URL=http://127.0.0.1:8000
API_KEY=your_random_key
```

SQLite hanya jalur belajar cepat. PostgreSQL adalah konfigurasi container utama.

4. Jalankan backend dan UI pada **dua terminal berbeda**:

```powershell
.\.venv\Scripts\python.exe -m uvicorn psh.api:app --reload
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

5. Buka http://localhost:8501. Klik **Buat dataset demo**, pilih dataset, lalu **Jalankan perbandingan**. Dokumentasi REST: http://localhost:8000/docs; header `X-API-Key` diperlukan pada endpoint selain health. Gunakan contoh `docs/API.md` atau koleksi Postman.
6. Notebook: buka `notebooks/01_minvola_replication.ipynb`, pilih interpreter `.venv`, lalu Run All. Notebook memanggil modul algoritma yang sama dengan backend agar implementasi tidak bercabang.
7. Jalankan verifikasi:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.execute_notebook
```

Tidak wajib menjalankan Activate.ps1; perintah interpreter eksplisit menghindari masalah execution policy PowerShell.

## Komponen

| File/folder | Peran |
|---|---|
| `psh/data.py` | Validasi CSV, daily return, statistik sesuai Appendix A, pemisahan kronologis |
| `psh/heuristic.py` | Heuristik Appendix C mode literal/koreksi, evaluasi constraint, solver kontinu |
| `psh/qubo.py` | QUBO paper, SA, steepest, tabu, random, exact enumeration kecil, QAOA statevector |
| `psh/quantum.py` | Sirkuit Qiskit dan adapter DWaveCliqueSampler opsional |
| `psh/ai.py` | Random Forest allocation surrogate + AI sebagai warm start |
| `psh/experiment.py` | Perbandingan, test di luar periode pengembangan, provenance |
| `psh/api.py` | Dataset upload, demo, eksperimen, histori melalui REST |
| `psh/database.py` | Tabel dataset, daily returns, runs, allocations melalui SQLAlchemy |
| `app.py` | Streamlit client yang memanggil FastAPI |
| `sql/analysis.sql` | Query SQL analisis data dan hasil |
| `deplyment.md` | Panduan deployment Docker dan cloud |
| `docs/REPLICATION.md` | Pemetaan paper versus implementasi |
| `docs/DATASETS.md` | Rekomendasi data gratis, tautan dan pengolahannya |

## Metode yang dibandingkan

- Problem-specific heuristic: n titik awal, tambah delta, pilih varians minimum di antara kandidat dengan return memadai; fallback return tertinggi; normalisasi; validasi akhir.
- Continuous SLSQP: acuan formulasi kontinu, **bukan sertifikat optimum diskret**.
- QUBO random sampling, simulated annealing, steepest descent, tabu search.
- Exact discrete grid: enumerasi seluruh bitstring untuk <=16 bit; optimum terbukti pada grid asli tersebut, sebelum normalisasi.
- QAOA: simulator statevector NumPy ideal, p=1..3, strategi LR/COBYLA/grid. Sirkuit Qiskit opsional menggunakan QUBO yang sama.
- AI comparator: Random Forest belajar pemetaan statistik → bobot dari label solver kontinu.
- AI complement: solver dimulai dari prediksi AI, lalu pilih varians minimum dari hasil solver tersebut dan heuristik. Biaya solver dan training dilaporkan; peningkatan bukan otomatis berkat AI.

## Alur aplikasi

CSV/demo → validasi → simpan daily return ke PostgreSQL → split waktu 60/20/20 → statistik pre-test → heuristik/solver/QUBO → training AI pada train dan tuning pada validation → periksa kelayakan → evaluasi test → simpan hasil/bobot → dashboard.

Data nyata tidak dibundel. `data/demo_returns.csv` adalah **sintetis**, dibuat dengan seed 42. Semua return dalam satuan desimal (0.01 = 1%).

## GitHub

Repository GitHub: https://github.com/rifqironanda/project-Problem-specific-Heuristic

Untuk menggunakan repository yang sudah tersedia:

```powershell
git clone https://github.com/rifqironanda/project-Problem-specific-Heuristic.git
cd project-Problem-specific-Heuristic
```

Script berikut hanya untuk membuat salinan repository pada akun lain. Setelah memasang GitHub CLI dan login:

```powershell
gh auth login
.\scripts\publish_github.ps1
```

Script membuat **private** repository `project-Problem-specific-Heuristic` pada akun yang login, lalu push. Jika sudah ada, script berhenti tanpa menimpa. Untuk publikasi portofolio, tinjau dahulu lalu ubah visibility di GitHub. Linux/macOS: `bash scripts/publish_github.sh`.

Panduan deployment lengkap, Docker, PostgreSQL, VM/cloud, backup dan pembaruan tersedia di `deplyment.md`.
