# Deployment aplikasi, Docker dan server/cloud

Nama file `deplyment.md` mengikuti permintaan. Semua langkah berikut adalah panduan; aplikasi belum dipublikasikan ke cloud dari sesi pembuatan proyek.

## 1. Persiapan lokal dan VS Code

Install Python 3.12, Git, Docker Desktop (Windows: aktifkan WSL2), VS Code + Python/Jupyter. Buka folder proyek. Gunakan interpreter `.venv`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
Copy-Item .env.example .env
```

Edit `.env`. Gunakan password PostgreSQL alfanumerik acak agar URL tidak memerlukan percent-encoding. Buat password/key masing-masing dengan:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(24))"
```

Jangan commit `.env`; `.gitignore` sudah mengecualikannya.

## 2. Docker Compose — API + UI + PostgreSQL

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs api
```

UI http://localhost:8501; API http://localhost:8000/docs. Layanan db menunggu healthcheck; API membuat schema lewat SQLAlchemy; UI memanggil API dengan key dari environment server. PostgreSQL menyimpan data pada named volume `pgdata`. Port hanya bind loopback, bukan seluruh interface.

1. Buat dataset demo melalui UI.
2. Jalankan eksperimen dan cek tabel feasible.
3. Restart `docker compose restart`, cek dataset/histori masih ada.
4. Unduh JSON hasil.

```powershell
docker compose exec db psql -U psh -d psh
```

Di psql: `\dt`, lalu query dari `sql/analysis.sql`. Jika `POSTGRES_USER`/DB diubah, sesuaikan command.

Berhenti tanpa membuang database:

```powershell
docker compose down
```

`down -v` menghapus volume; tidak diperlukan untuk deployment normal.

## 3. Python lokal + PostgreSQL container

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe -m uvicorn psh.api:app --reload
```

Terminal kedua:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`.env` harus memakai host `localhost` untuk Python lokal; compose memakai host service `db` untuk API container. Jangan menggunakan `--reload` pada server produksi.

## 4. Git dan GitHub

Repository lokal telah diinisialisasi. Jika memakai ZIP, folder `.git` tidak dibundel; script akan menginisialisasi ulang.

```powershell
winget install GitHub.cli
gh auth login
.\scripts\publish_github.ps1
```

Script menggunakan akun yang login, mengecek nama, membuat private repository bila belum ada dan push. Repository utama tersedia di https://github.com/rifqironanda/project-Problem-specific-Heuristic; gunakan git clone untuk mulai. Script pembuatan repo hanya diperlukan untuk salinan di akun lain. Linux: `bash scripts/publish_github.sh`.

Untuk update setelah remote dibuat:

```powershell
git add .
git commit -m "Describe your change"
git push origin main
```

GitHub Actions menjalankan pytest, PostgreSQL integration dan notebook. GitHub Pages hanya hosting static; backend FastAPI, PostgreSQL dan training Python memerlukan server/container.

## 5. Server Linux / VM cloud (jalur utama)

Gunakan VM Ubuntu dengan Docker Engine + Compose plugin. Saran awal untuk lab: 2 CPU / 4 GB RAM; simulator statevector dibatasi 14 qubit. Jangan menganggap cloud pasti gratis; pilih resource sesuai kuota dan hentikan layanan yang tidak diperlukan.

```bash
git clone https://github.com/YOUR_ACCOUNT/project-Problem-specific-Heuristic.git
cd project-Problem-specific-Heuristic
cp .env.example .env
# Edit .env dengan key/password baru pada server.
docker compose up --build -d
curl http://127.0.0.1:8000/health
```

Untuk repo private, gunakan GitHub CLI login/deploy key yang berhak membaca, bukan menaruh token di URL clone. Gunakan firewall yang hanya membuka SSH dan HTTP(S). PostgreSQL/API/UI tetap loopback melalui compose.

### Akses lab melalui SSH tunnel

Jalankan dari laptop:

```bash
ssh -L 8501:127.0.0.1:8501 -L 8000:127.0.0.1:8000 USER@SERVER_IP
```

Buka localhost:8501 di laptop. Ini jalur penggunaan pribadi tanpa membuka aplikasi ke internet.

### Akses publik melalui HTTPS

Pasang reverse proxy yang mendukung WebSocket (Caddy atau Nginx), domain dan TLS. Contoh konfigurasi Caddy di server:

```caddyfile
portfolio.example.com {
    reverse_proxy 127.0.0.1:8501
}
```

Untuk akses publik, tambahkan autentikasi pengguna/akses di reverse proxy atau identity provider **sebelum** membuka domain. API key melindungi backend, tetapi bukan login pengguna dashboard: siapa pun yang bisa membuka UI dapat menjalankan permintaan memakai key server. Batasi upload, concurrency dan waktu job. Contoh konfigurasi di atas routing saja, bukan akses kontrol yang lengkap.

Jika API perlu dapat diakses langsung dari klien lain, gunakan hostname terpisah dengan TLS serta X-API-Key; jangan taruh key pada JavaScript publik. Backend tidak perlu dibuka untuk UI karena komunikasi terjadi server-to-server.

## 6. Container platform + managed PostgreSQL (alternatif cloud)

Platform dapat berupa layanan container terkelola yang mendukung Docker dan managed PostgreSQL. Langkah netral provider:

1. Buat PostgreSQL dan simpan connection string sebagai secret `DATABASE_URL=postgresql+psycopg://...`. Tambahkan SSL parameter sesuai provider (`?sslmode=require` jika dipersyaratkan).
2. Deploy image Dockerfile sebagai API. Start command: `python -m uvicorn psh.api:app --host 0.0.0.0 --port 8000`. Sesuaikan port environment platform bila platform mensyaratkan `$PORT`.
3. Isi API_KEY secret yang sama pada API dan UI. Cek `/health`.
4. Deploy image yang sama sebagai UI. Command: `python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501`. Set API_BASE_URL ke alamat backend yang dapat dicapai dari container UI.
5. Hubungkan HTTPS/auth, resource limits, persistent DB, logging dan backup. Test upload dan run end-to-end.
6. Harga, free tier dan kebijakan sleep berubah; periksa dokumentasi provider sebelum memilih. Proyek ini tidak membuat akun/resource berbayar.

## 7. Backup PostgreSQL dan pemulihan

Linux/server: stream dump agar tidak melalui encoding redirection Windows PowerShell lama.

```bash
docker compose exec -T db pg_dump -U psh -d psh -Fc > psh.backup
```

Windows: buat file di container lalu copy byte-nya:

```powershell
docker compose exec db pg_dump -U psh -d psh -Fc -f /tmp/psh.backup
docker compose cp db:/tmp/psh.backup ./psh.backup
```

Untuk restore ke database **baru/kosong**:

```powershell
docker compose cp ./psh.backup db:/tmp/psh.backup
docker compose exec db pg_restore -U psh -d RESTORE_DB --no-owner /tmp/psh.backup
```

Buat RESTORE_DB dahulu, cek hasil, baru pilih database yang dipakai aplikasi. Jangan menimpa database aktif tanpa backup terverifikasi.

## 8. Update dan rollback

Sebelum update: backup DB, catat commit `git rev-parse HEAD`. Lalu `git pull --ff-only`, jalankan test, `docker compose up --build -d`. Cek health, dataset dan eksperimen. Rollback kode dengan checkout commit terdahulu dan rebuild. Schema saat ini memakai create_all, bukan migration; perubahan schema berikutnya memerlukan Alembic migration yang diuji. Jangan menganggap rollback kode membatalkan perubahan data/schema.

## 9. Quantum opsional

Default proyek tidak mengirim job kuantum. Install `pip install -e ".[quantum]"` hanya bila ingin memakai sirkuit Qiskit/adapter D-Wave. Kredensial Leap diperlukan untuk hardware D-Wave. Fungsi `psh.quantum.dwave_sample` akan mengirim job saat dipanggil eksplisit; entitlement/biaya ditentukan akun. Hardware IBM belum disediakan sebagai workflow runtime terintegrasi. QAOA notebook tetap bisa dijalankan secara gratis di simulator lokal.

## 10. Status validasi

Lihat `docs/VALIDATION.md` untuk hasil pytest, notebook, REST dan batas lingkungan. Docker/VM/cloud tidak dinyatakan berhasil jika tidak dijalankan. Tidak ada deployment cloud yang dilakukan dalam sesi ini.
