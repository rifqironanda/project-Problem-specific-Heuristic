# Validasi proyek

Tanggal: 12 Oktober 2026. Lingkungan Python 3.12.14.

- Pytest: **15 passed, 1 skipped**. Mencakup formulasi statistik paper, constraint, typo normalisasi, QUBO identity seluruh bitstring kecil, seed repeatability, AI chronology/projection, REST dataset→experiment→database→history, autentikasi/validasi, UI demo→run, dan kesetaraan probabilitas sirkuit Qiskit versus simulator biaya/mixer.
- PostgreSQL integration test disediakan dan dijalankan CI dengan service PostgreSQL, tetapi **belum dijalankan lokal**: tidak ada server PostgreSQL dan lingkungan menolak instalasi/start layanan. Test lokal menggunakan SQLite.
- Notebook: **11 code cells berhasil dieksekusi seluruhnya**, 27 output tersimpan (tabel/plot/hasil). Executor IPython in-process karena lingkungan menolak TCP/IPC socket kernel Jupyter. Skrip NotebookClient standar disediakan untuk VS Code/CI; peluncuran kernel standar belum diverifikasi di lingkungan ini.
- Dependency lock (92 packages) berhasil dibuat dan dipasang; test kemudian diulang dengan dependency lock.
- API diverifikasi dengan FastAPI TestClient; UI dengan Streamlit AppTest yang memanggil API test client. Layanan HTTP nyata tidak dijalankan karena socket dibatasi.
- QAOA simulator diuji; sirkuit Qiskit 2.5.2 diuji terhadap simulator. D-Wave/IBM QPU belum dijalankan. Adapter D-Wave bersifat opsional dan belum diverifikasi hardware.
- Python compileall dan bash syntax check berhasil. Compose YAML dapat diparse dan memiliki healthcheck/dependency internal; **docker compose build/up belum dijalankan** karena Docker tidak tersedia.
- Unduhan real dataset Kenneth French berhasil: **1.006 hari × 30 portofolio industri**, periode 2020–2023. Pipeline tambahan diuji pada 6 kolom pertama dengan d=3; hasil tersimpan di data/french_example_report.json. Dataset mentah tidak dibundel/di-commit. VM/cloud belum dijalankan.
- Repository GitHub dibuat oleh pemilik akun dan proyek diunggah ke rifqironanda/project-Problem-specific-Heuristic. Skrip publish untuk akun lain tetap tersedia. Hasil CI remote dilaporkan terpisah dari validasi lokal.

## Hasil demo (bukan bukti pasar)

Seed 42, 6 aset sintetis, d=1, reads=50/sweeps=50.

| Metode | Layak | Varians tahunan |
|---|---:|---:|
| problem_specific_heuristic | True | 0.004395263369096781 |
| continuous_slsqp | True | 0.003150870066505888 |
| equal_weight | False | 0.0033839656680301066 |
| ai_surrogate | False | 0.0030692492208874217 |
| ai_complement_heuristic | True | 0.003150870066076452 |
| qubo_random | False | — |
| qubo_sa | True | 0.004395263369096781 |
| qubo_steepest | True | 0.004395263369096781 |
| qubo_tabu | True | 0.004395263369096781 |
| exact_discrete_grid | True | 0.004395263369096781 |
| qaoa_classical_simulator | True | 0.004428912299333867 |

AI surrogate tidak memenuhi target pada demo ini; hasil infeasible tetap dilaporkan. Hybrid melibatkan SLSQP, sehingga varians yang lebih baik bukan bukti keunggulan AI. Budget demo bukan benchmark fixed-time paper.

## Versi paket utama

```json
{
  "numpy": "2.3.5",
  "pandas": "2.2.3",
  "scipy": "1.17.0",
  "scikit-learn": "1.8.0",
  "fastapi": "0.143.0",
  "sqlalchemy": "2.1.4",
  "streamlit": "1.65.0",
  "qiskit": "2.5.2",
  "nbformat": "5.11.1"
}
```
