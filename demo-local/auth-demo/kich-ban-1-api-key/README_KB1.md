# KỊCH BẢN 1: PHÂN QUYỀN API KEY — SO SÁNH 3 ROLE

> Mục tiêu: Chứng minh Qdrant có 3 mức phân quyền rõ ràng khi bật API Key. Mỗi role test nhanh 1 thao tác đọc + 1 thao tác ghi để thấy sự khác biệt.

---

## BƯỚC 1: Khởi động Qdrant với phân quyền

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

### 1.2 Start Qdrant

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
docker compose up -d
docker compose ps
```

### 1.3 Verify

```cmd
curl.exe http://localhost:6380/healthz
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

## BƯỚC 4: TEST — ANONYMOUS (Không có key)

### 4.1 Anonymous → Đọc collections

```cmd
curl.exe http://localhost:6380/collections
```

**Mong đợi:** ❌ 401 Unauthorized
```json
{"status":{"error":"Must provide an API key or an Authorization bearer token"},"time":0.0}
```

### 4.2 Anonymous → Search

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -d @queries\query_dense.json
```

**Mong đợi:** ❌ 401 — Không key thì không làm gì được.

---

## BƯỚC 5: TEST — ADMIN KEY

### 5.1 Admin → Đọc collections

```cmd
curl.exe "http://localhost:6380/collections" -H "api-key: admin-secret-key-2024"
```

**Mong đợi:** ✅ 200 — Trả về danh sách collections.

### 5.2 Admin → Search

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -H "api-key: admin-secret-key-2024" -d @queries\query_dense.json
```

**Mong đợi:** ✅ 200 — Kết quả search bình thường.

### 5.3 Admin → Upsert

> Dùng script Python để tạo point với vector đúng 384 chiều:

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\test_upsert.py --key admin-secret-key-2024
```

**Mong đợi:** ✅ 200 — Ghi thành công.

### 5.4 Admin → Xóa point vừa thêm

```cmd
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/delete" -H "Content-Type: application/json" -H "api-key: admin-secret-key-2024" -d "{\"points\":[9999]}"
```

**Mong đợi:** ✅ 200 — Xóa thành công.

---

## BƯỚC 6: TEST — READ-ONLY KEY

### 6.1 Read-only → Đọc collections

```cmd
curl.exe "http://localhost:6380/collections" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ✅ 200 — Đọc được.

### 6.2 Read-only → Search

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
curl.exe -X POST "http://localhost:6380/collections/auth_demo/points/query" -H "Content-Type: application/json" -H "api-key: readonly-key-2024" -d @queries\query_dense.json
```

**Mong đợi:** ✅ 200 — Search được.

### 6.3 Read-only → Upsert (GHI)

> Dùng script Python (sẽ bị 403):

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\test_upsert.py --key readonly-key-2024
```

**Mong đợi:** ❌ 403 Forbidden — Không có quyền ghi.

### 6.4 Read-only → Xóa collection

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/auth_demo" -H "api-key: readonly-key-2024"
```

**Mong đợi:** ❌ 403 Forbidden — Không có quyền xóa.

---

## BƯỚC 7: Cleanup

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/auth_demo" -H "api-key: admin-secret-key-2024"
cd /d D:\Qdrant\demo-local\auth-demo
docker compose down
```

---

## BẢNG TỔNG KẾT

| Thao tác | Anonymous (No Key) | Read-only Key | Admin Key |
|----------|-------------------|---------------|-----------|
| Đọc collections | ❌ 401 | ✅ 200 | ✅ 200 |
| Search | ❌ 401 | ✅ 200 | ✅ 200 |
| Upsert (ghi) | ❌ 401 | ❌ 403 | ✅ 200 |
| Delete (xóa) | ❌ 401 | ❌ 403 | ✅ 200 |

**Kết luận:**
- **Anonymous:** Bị chặn hoàn toàn (401)
- **Read-only:** Đọc OK, ghi bị cấm (403)
- **Admin:** Full quyền

> Chi tiết Read-only key (16 test cases) → xem [Kịch bản 1B](../kich-ban-1b-readonly-key/README_KB1B.md)
