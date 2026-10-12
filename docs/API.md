# REST API dan Postman

Backend http://127.0.0.1:8000. Swagger: `/docs`. Kecuali `/health`, semua route memerlukan `X-API-Key` bila `API_KEY` di-set. Header ini bisa ditambahkan secara manual di Swagger (Parameters) atau gunakan Postman collection `docs/postman_collection.json`.

| Method | Route | Fungsi |
|---|---|---|
| GET | `/health` | Cek backend dan database |
| POST | `/datasets/demo` | Generate dan simpan demo sintetis |
| POST | `/datasets` | Multipart `file` CSV dan `kind`=returns/prices |
| GET | `/datasets` | 100 dataset terbaru |
| POST | `/experiments` | Olah data, training, optimasi, simpan hasil |
| GET | `/experiments` | 100 eksperimen terbaru |
| GET | `/experiments/{id}` | Ambil hasil lengkap |

PowerShell:

```powershell
$headers = @{ 'X-API-Key' = 'your_random_key' }
$ds = Invoke-RestMethod -Method Post -Uri http://localhost:8000/datasets/demo -Headers $headers
$body = @{ dataset_id=$ds.id; d=1; seed=42; reads=100; sweeps=100; include_quantum=$false } | ConvertTo-Json
$run = Invoke-RestMethod -Method Post -Uri http://localhost:8000/experiments -Headers $headers -ContentType application/json -Body $body
$run.results | Select-Object method,feasible,variance,runtime_seconds
```

`target=null`: quantile 70% pre-test geometric annual return. `delta=null`: ub/2^d. `max_weight=null`: formula paper. Field target/variance tahunan; delta dan weight berupa proporsi dana.

Status: 401 key salah; 404 dataset/run tidak ada; 413 CSV terlalu besar; 422 kontrak/parameter gagal. Target terlalu tinggi dapat memberi hasil `feasible=false`, bukan exception. Hasil infeasible tidak diberi metrik held-out.

Eksekusi sinkron untuk dataset kecil. Untuk banyak pengguna/benchmark besar, pindahkan eksperimen ke worker queue dan simpan status job. Endpoint ini belum menyediakan multiuser ownership atau penghapusan data; API key shared hanya cukup untuk lab pribadi.
