# KỊCH BẢN 2: JWT PHÂN QUYỀN THEO COLLECTION

> Mục tiêu: Tạo JWT token giới hạn truy cập vào 1 collection cụ thể. Token HR chỉ thao tác được trên `hr_docs`, Token IT chỉ trên `it_docs`.

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

> **Quan trọng:** `JWT_RBAC=true` phải bật để Qdrant chấp nhận JWT tokens.

### 1.2 Cài thêm thư viện PyJWT (nếu chưa có)

```cmd
D:\Qdrant\.venv\Scripts\pip.exe install PyJWT
```

### 1.3 Start

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
docker compose up -d
docker compose ps
```

---

## BƯỚC 2: Tạo JWT Tokens (dùng script Python)

> **Lưu ý:** Trên single-node, Qdrant dùng chính API Key (`admin-secret-key-2024`) làm secret để verify JWT.
> Endpoint `/cluster/secret-key` chỉ hoạt động ở cluster mode.

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-2-jwt-collection
D:\Qdrant\.venv\Scripts\python.exe generate_tokens.py
```

Khi script hỏi "Nhập JWT secret key" → nhập: `admin-secret-key-2024`

Script tạo:
- `token_hr.txt` - Token chỉ truy cập collection `hr_docs` (read + write)
- `token_it.txt` - Token chỉ truy cập collection `it_docs` (read + write)

---

## BƯỚC 4: Admin tạo 2 collections + upsert data

### 4.1 Tạo collections

```cmd
curl.exe -X PUT "http://localhost:6380/collections/hr_docs" -H "Content-Type: application/json" -H "api-key: admin-secret-key-2024" -d "{\"vectors\":{\"dense\":{\"size\":384,\"distance\":\"Cosine\"}},\"sparse_vectors\":{\"keywords\":{}}}"

curl.exe -X PUT "http://localhost:6380/collections/it_docs" -H "Content-Type: application/json" -H "api-key: admin-secret-key-2024" -d "{\"vectors\":{\"dense\":{\"size\":384,\"distance\":\"Cosine\"}},\"sparse_vectors\":{\"keywords\":{}}}"
```

### 4.2 Generate vectors + upload data cho từng collection

Chạy script upload riêng cho kịch bản 2:

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-2-jwt-collection
D:\Qdrant\.venv\Scripts\python.exe setup_data.py
```

Script này sẽ sinh embeddings cho sample documents rồi upsert vào `hr_docs` và `it_docs`.

---

## BƯỚC 5: Sinh query embeddings

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\generate_query.py
```

Nhập câu hỏi: `Hướng dẫn nghỉ phép`

---

## BƯỚC 6: TEST PHÂN QUYỀN JWT

### 6.1 Token HR → Search `hr_docs` (thành công) ✅

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-2-jwt-collection
set /p TOKEN_HR=<token_hr.txt
curl.exe -X POST "http://localhost:6380/collections/hr_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_HR%" -d @..\queries\query_dense.json
```

**Mong đợi:** ✅ Trả về kết quả search từ `hr_docs`.

---

### 6.2 Token HR → Search `it_docs` (BỊ TỪ CHỐI) ❌

```cmd
curl.exe -X POST "http://localhost:6380/collections/it_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_HR%" -d @..\queries\query_dense.json
```

**Mong đợi:** ❌ 403 Forbidden - Token HR không có quyền truy cập `it_docs`.

---

### 6.3 Token IT → Search `it_docs` (thành công) ✅

```cmd
set /p TOKEN_IT=<token_it.txt
curl.exe -X POST "http://localhost:6380/collections/it_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_IT%" -d @..\queries\query_dense.json
```

**Mong đợi:** ✅ Trả về kết quả từ `it_docs`.

---

### 6.4 Token IT → Search `hr_docs` (BỊ TỪ CHỐI) ❌

```cmd
curl.exe -X POST "http://localhost:6380/collections/hr_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_IT%" -d @..\queries\query_dense.json
```

**Mong đợi:** ❌ 403 Forbidden.

---

### 6.5 Token HR → Upsert vào `hr_docs` (thành công) ✅

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-2-jwt-collection
D:\Qdrant\.venv\Scripts\python.exe test_upsert_jwt.py --token-file token_hr.txt --collection hr_docs
```

**Mong đợi:** ✅ Upsert thành công (token HR có quyền rw trên hr_docs).

---

### 6.6 Token IT → Upsert vào `hr_docs` (BỊ TỪ CHỐI) ❌

```cmd
D:\Qdrant\.venv\Scripts\python.exe test_upsert_jwt.py --token-file token_it.txt --collection hr_docs
```

**Mong đợi:** ❌ 403 Forbidden.

---

### 6.7 Token HR → Xóa collection (BỊ TỪ CHỐI) ❌

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/hr_docs" -H "Authorization: Bearer %TOKEN_HR%"
```

**Mong đợi:** ❌ 403 Forbidden (JWT token không có quyền delete collection, chỉ admin key mới được).

---

## BƯỚC 7: Cleanup

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/hr_docs" -H "api-key: admin-secret-key-2024"
curl.exe -X DELETE "http://localhost:6380/collections/it_docs" -H "api-key: admin-secret-key-2024"
cd /d D:\Qdrant\demo-local\auth-demo
docker compose down
```

---

## BẢNG TỔNG KẾT

| Hành động | Token HR | Token IT | Admin Key |
|-----------|----------|----------|-----------|
| Search hr_docs | ✅ | ❌ 403 | ✅ |
| Search it_docs | ❌ 403 | ✅ | ✅ |
| Upsert hr_docs | ✅ | ❌ 403 | ✅ |
| Upsert it_docs | ❌ 403 | ✅ | ✅ |
| Delete collection | ❌ 403 | ❌ 403 | ✅ |
| Scroll hr_docs | ✅ | ❌ 403 | ✅ |
| Scroll it_docs | ❌ 403 | ✅ | ✅ |
