
# KỊCH BẢN DEMO QDRANT - DÙNG POWERSHELL (WINDOWS)

> Không cần Python. Chỉ dùng Docker + PowerShell (có sẵn trên Windows).
>
> Nếu bạn muốn chạy bằng Command Prompt (CMD) thay vì PowerShell, hãy xem file [README_CMD.md](README_CMD.md).

## Thông tin máy
| Thông số | Giá trị |
|----------|---------|
| CPU | Intel i7-1165G7 (4 cores / 8 threads) |
| RAM | 16 GB |
| Ổ D: trống | ~155 GB |
| Docker | v29.1.3 (Docker Desktop) |
| OS | Windows 11 |

## Tài nguyên sử dụng
| Thành phần | RAM | Ghi chú |
|------------|-----|---------|
| Qdrant container | max 2 GB | Giới hạn trong docker-compose |
| Docker Desktop | ~1.5 GB | Base overhead |
| **Tổng thêm** | **~3.5 GB** | Máy vẫn còn ~12 GB cho Windows |

→ **Máy 16GB chạy thoải mái, không lag.**

---

## BƯỚC 0: Khởi động Docker Desktop
- Mở Docker Desktop từ Start Menu
- Đợi icon Docker ở taskbar chuyển xanh lá (Running)

---

## BƯỚC 1: Start Qdrant

```powershell
cd D:\Qdrant\demo-local
docker compose up -d
```

Kiểm tra:
```powershell
docker compose ps
```

Mở browser: http://localhost:6333/dashboard

---

## BƯỚC 2: Health check

```powershell
Invoke-RestMethod -Uri "http://localhost:6333/healthz"
```

```powershell
Invoke-RestMethod -Uri "http://localhost:6333"
```

---

## BƯỚC 3: Tạo Collection

```powershell
$body = @{
    vectors = @{
        dense = @{
            size = 384
            distance = "Cosine"
        }
    }

    sparse_vectors = @{
        keywords = @{}
    }

    shard_number = 1
    replication_factor = 1
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
-Method Put `
-Uri "http://localhost:6333/collections/smart_search_demo" `
-ContentType "application/json" `
-Body $body
```

Kiểm tra:
```powershell
Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_demo"
```

---

## BƯỚC 4: Tạo Payload Indexes (filter nhanh)

```powershell
$fields = @("doc_status", "domain", "department", "doc_type")

foreach ($field in $fields) {
    $body = @{
        field_name = $field
        field_schema = "keyword"
    } | ConvertTo-Json

    Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_demo/index" -ContentType "application/json" -Body $body
    Write-Host "Created index: $field"
}
```

---

## BƯỚC 5: Upsert dữ liệu mẫu

### 5A. Workflow production-style: từ documents sang points

Thay vì lưu vector ngẫu nhiên thủ công trong JSON, demo mới sử dụng dữ liệu gốc ở dạng documents và tự động sinh dense + sparse embeddings.

Các file mới:
- sample_data\documents_batch_01.json
- sample_data\documents_batch_02.json
- sample_data\generate_vectors.py

Tạo các file points đã embedding:

```powershell
cd D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\generate_vectors.py
```

Kết quả sẽ tạo:
- sample_data\points_batch_01.json
- sample_data\points_batch_02.json

### 5B. Upsert dữ liệu mẫu vào Qdrant

Khuyến nghị dùng script Python UTF-8-safe đã chuẩn bị sẵn:

```powershell
cd D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\upload_to_qdrant.py
```

Script này sẽ:
- xóa collection cũ nếu có
- tạo lại collection mới
- upsert cả 2 batch points vào Qdrant
- kiểm tra payload sau khi upload

Nếu bạn muốn thử thủ công bằng PowerShell, hãy nhớ rằng đây là vùng dễ bị lỗi mã hóa. Vì vậy khuyến nghị chính vẫn là dùng script Python đã chuẩn bị sẵn. Nếu vẫn muốn thử, hãy dùng phương thức dưới đây với UTF-8 và chú ý xóa collection cũ trước khi upsert lại:

```powershell
# Batch 1: domain nhan_su (6 points)
$json1 = [System.IO.File]::ReadAllText(
    (Resolve-Path ".\sample_data\points_batch_01.json").Path,
    [System.Text.Encoding]::UTF8
)

Invoke-RestMethod `
    -Method Put `
    -Uri "http://localhost:6333/collections/smart_search_demo/points?wait=true" `
    -ContentType "application/json; charset=utf-8" `
    -Body $json1

# Batch 2: domain cong_nghe + hanh_chinh (6 points)
$json2 = [System.IO.File]::ReadAllText(
    (Resolve-Path ".\sample_data\points_batch_02.json").Path,
    [System.Text.Encoding]::UTF8
)

Invoke-RestMethod `
    -Method Put `
    -Uri "http://localhost:6333/collections/smart_search_demo/points?wait=true" `
    -ContentType "application/json; charset=utf-8" `
    -Body $json2
```

> Nếu bạn đã từng upsert dữ liệu bằng cách đọc file với encoding sai, Qdrant sẽ giữ dữ liệu lỗi đó trong collection. Khi đổi sang UTF-8, hãy xóa collection cũ rồi tạo lại trước khi upsert lại:
>
```powershell
Invoke-RestMethod -Method Delete -Uri "http://localhost:6333/collections/smart_search_demo"
```
>
Sau đó chạy lại các bước tạo collection và upsert từ đầu.

Kiểm tra số lượng points:
```powershell
(Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_demo").result.points_count
```
→ Kết quả: 12

---
Invoke-RestMethod `
-Uri "http://localhost:6333/collections/smart_search_demo/points/scroll" `
-Method Post `
-ContentType "application/json" `
-Body '{"limit":100,"with_payload":true,"with_vector":true}' | ConvertTo-Json -Depth 100

## BƯỚC 6: Hybrid Search (Dense + Sparse)

### 6.1 Search cơ bản (không filter)
```powershell
$query = Get-Content -Raw -Path "queries\search_basic.json"
Invoke-RestMethod `
-Method Post `
-Uri "http://localhost:6333/collections/smart_search_demo/points/query" `
-ContentType "application/json" `
-Body $query |
ConvertTo-Json -Depth 10
```

### 6.2 Search + Filter theo domain = cong_nghe
```powershell
$query = Get-Content -Raw -Path "queries\search_filter_domain.json"

Invoke-RestMethod `
-Method Post `
-Uri "http://localhost:6333/collections/smart_search_demo/points/query" `
-ContentType "application/json" `
-Body $query |
ConvertTo-Json -Depth 10
```

### 6.3 Search + Filter theo department = NHAN_SU
```powershell
$query = Get-Content -Raw -Path "queries\search_filter_department.json"

Invoke-RestMethod `
-Method Post `
-Uri "http://localhost:6333/collections/smart_search_demo/points/query" `
-ContentType "application/json" `
-Body $query |
ConvertTo-Json -Depth 10
```

### 6.4 Search + Multi-filter (domain + doc_status + doc_type)
```powershell
$query = Get-Content -Raw -Path "queries\search_multi_filter.json"
Invoke-RestMethod `
-Method Post `
-Uri "http://localhost:6333/collections/smart_search_demo/points/query" `
-ContentType "application/json" `
-Body $query |
ConvertTo-Json -Depth 10
```

---

## BƯỚC 7: Scroll (liệt kê points có payload)

```powershell
$body = @{
    limit = 5
    with_payload = $true
    with_vector = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_demo/points/scroll" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10
```

---

## BƯỚC 8: Update payload (đổi trạng thái văn bản)

Ví dụ: đổi doc_status từ ACTIVE → ARCHIVED cho points 1, 2, 3
```powershell
$body = @{
    payload = @{ doc_status = "ARCHIVED" }
    points = @(1, 2, 3)
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_demo/points/payload" -ContentType "application/json" -Body $body
```

Kiểm tra: search lại với filter `doc_status=ACTIVE` → sẽ không thấy point 1,2,3.

---

## BƯỚC 9: Delete points

```powershell
$body = @{
    points = @(1, 2, 3)
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_demo/points/delete" -ContentType "application/json" -Body $body
```

---

## BƯỚC 10: Snapshot (backup)

Tạo snapshot:
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_demo/snapshots"
```

Liệt kê snapshots:
```powershell
Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_demo/snapshots"
```

---

## BƯỚC 11: Xóa Collection (cleanup)

```powershell
Invoke-RestMethod -Method Delete -Uri "http://localhost:6333/collections/smart_search_demo"
```

---

## BƯỚC 12: Dừng Qdrant

```powershell
cd D:\Qdrant\demo-local
docker compose down
```

Data vẫn giữ trong `qdrant_storage\`. Chạy lại `docker compose up -d` là có ngay.

---

## TÓM TẮT LUỒNG DEMO

```
[Start Qdrant] → [Tạo Collection] → [Tạo Indexes]
       → [Upsert Data] → [Search + Filter]
       → [Update Payload] → [Delete] → [Snapshot]
       → [Cleanup]
```

## SO SÁNH VỚI PRODUCTION

| Demo (local) | Production (cluster) |
|---|---|
| 1 node, 1 shard, no replica | 4 nodes, 4 shards, replica=2 |
| 384d vectors (giả lập) | 1024d (BGE-M3) + sparse vectors |
| Không auth | API key + TLS |
| 12 vectors | 8-10M vectors |
| PowerShell trực tiếp | qua Load Balancer + gRPC |
| Không quantization | INT8 Scalar Quantization |
| Không cluster | 4 VMs × 48GB RAM |
=======
