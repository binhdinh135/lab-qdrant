# KỊCH BẢN 1B: READ-ONLY API KEY - TEST CHI TIẾT (16 TEST CASES)

> Mục tiêu: Demo đầy đủ những gì Read-only Key **được phép** và **bị cấm**. Giả lập ứng dụng frontend chỉ có quyền tìm kiếm.

---

## BƯỚC 1: Khởi động Qdrant

### 1.1 Nội dung docker-compose.yml

```yaml
services:
  qdrant-auth:
    image: qdrant/qdrant:v1.12.0
    container_name: qdrant-auth-demo
    ports:
      - "6380:6333"
      - "6381:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__API_KEY=admin-secret-key-2024
      - QDRANT__SERVICE__READ_ONLY_API_KEY=readonly-key-2024
      - QDRANT__SERVICE__JWT_RBAC=true
```

### 1.2 Start

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
docker compose up -d
docker compose ps
```

---

## BƯỚC 2: Sinh data và upload

### 2.1 Generate vectors (nếu chưa có)

```cmd
cd /d D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe sample_data\generate_vectors.py
```

### 2.2 Setup collection + upload

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\setup_collection.py
```

---

## BƯỚC 3: Sinh query embeddings

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\generate_query.py
```

Nhập câu hỏi: `Hướng dẫn nghỉ phép`

---

## BƯỚC 4: TEST ĐỌC (Read-only Key = `readonly-key-2024`) - TẤT CẢ PHẢI THÀNH CÔNG

### Test 1: Liệt kê collections ✅

```cmd
curl.exe "http://localhost:6380/collections" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ✅ Trả về danh sách collections.

---

### Test 2: Chi tiết collection ✅

```cmd
curl.exe "http://localhost:6380/collections/auth_demo" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ✅ Trả về info (vector size, số points, indexes...).

---

### Test 3: Dense search (dùng file query đã sinh) ✅

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d @queries\query_dense.json
```

**Mong đợi:** ✅ Trả về top 5 kết quả gần nhất.

---

### Test 4: Hybrid search (dense + sparse + RRF) ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d @queries\query_hybrid.json
```

**Mong đợi:** ✅ Trả về top 5 kết quả hybrid.

---

### Test 5: Search + Filter theo department ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d @queries\query_dense.json
```

> Hoặc dùng filter thủ công:

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/scroll" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"limit\":10,\"with_payload\":true,\"filter\":{\"must\":[{\"key\":\"department\",\"match\":{\"value\":\"NHAN_SU\"}}]}}"
```

**Mong đợi:** ✅ Chỉ trả về docs của NHAN_SU.

---

### Test 6: Scroll (phân trang) ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/scroll" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"limit\":3,\"with_payload\":true,\"with_vector\":false}"
```

**Mong đợi:** ✅ Trả về 3 points + `next_page_offset`.

---

### Test 7: Get point by ID ✅

```cmd
curl.exe "http://localhost:6380/collections/auth_demo/points/1" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ✅ Trả về point id=1.

---

### Test 8: Get multiple points ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"ids\":[1,2,3],\"with_payload\":true}"
```

**Mong đợi:** ✅ Trả về 3 points.

---

### Test 9: Count points ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/count" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"exact\":true}"
```

**Mong đợi:** ✅ Trả về tổng số points.

---

## BƯỚC 5: TEST GHI (Read-only Key) - TẤT CẢ PHẢI BỊ TỪ CHỐI

### Test 10: Upsert point ❌

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\test_upsert.py --key readonly-key-2024
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 11: Delete points ❌

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/delete" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"points\":[1,2]}"
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 12: Update payload ❌

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/payload" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"payload\":{\"title\":\"HACKED\"},\"points\":[1]}"
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 13: Tạo collection mới ❌

```cmd
curl.exe -X PUT "http://localhost:6380/collections/hacker_collection" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"vectors\":{\"dense\":{\"size\":4,\"distance\":\"Cosine\"}}}"
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 14: Xóa collection ❌

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/auth_demo" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 15: Tạo index ❌

```cmd
curl.exe -X PUT "http://localhost:6380/collections/auth_demo/index" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d "{\"field_name\":\"author\",\"field_schema\":\"keyword\"}"
```

**Mong đợi:** ❌ 403 Forbidden

---

### Test 16: Tạo snapshot ❌

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/snapshots" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ❌ 403 Forbidden

---

## BƯỚC 6: Cleanup

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/auth_demo" -H "api-key: admin-secret-key-2024"
cd /d D:\Qdrant\demo-local\auth-demo
docker compose down
```

---

## BẢNG TỔNG KẾT

### ✅ Được phép (9 thao tác đọc)

| # | Thao tác | Endpoint |
|---|----------|----------|
| 1 | Liệt kê collections | GET /collections |
| 2 | Chi tiết collection | GET /collections/{name} |
| 3 | Dense search | POST /points/query |
| 4 | Hybrid search | POST /points/query |
| 5 | Search + filter | POST /points/scroll (filter) |
| 6 | Scroll | POST /points/scroll |
| 7 | Get point by ID | GET /points/{id} |
| 8 | Get multiple points | POST /points |
| 9 | Count points | POST /points/count |

### ❌ Bị cấm (7 thao tác ghi)

| # | Thao tác | Endpoint | HTTP |
|---|----------|----------|------|
| 10 | Upsert points | PUT /points | 403 |
| 11 | Delete points | POST /points/delete | 403 |
| 12 | Update payload | POST /points/payload | 403 |
| 13 | Create collection | PUT /collections/{name} | 403 |
| 14 | Delete collection | DELETE /collections/{name} | 403 |
| 15 | Create index | PUT /index | 403 |
| 16 | Create snapshot | POST /snapshots | 403 |
