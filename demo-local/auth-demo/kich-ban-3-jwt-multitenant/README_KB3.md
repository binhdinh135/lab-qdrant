# KỊCH BẢN 3: JWT MULTI-TENANT (Phân quyền theo Payload Filter)

> Mục tiêu: 1 collection duy nhất, mỗi user/team chỉ thấy data thuộc về mình thông qua JWT claim tự động filter payload. Mô phỏng hệ thống SaaS multi-tenant.

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

> **Quan trọng:** `JWT_RBAC=true` bắt buộc để JWT payload filter hoạt động.

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

## BƯỚC 2: Setup data (sinh embeddings + upload)

Script tạo collection `company_docs`, sinh embeddings cho documents đa phòng ban, upsert:

```cmd
cd /d D:\Qdrant\.venv\Scripts\python.exe kich-ban-3-jwt-multitenant\setup_data.py

```

Output mong đợi:
```
============================================================
SETUP DATA CHO KỊCH BẢN 3: MULTI-TENANT
============================================================
[1/3] Tạo collection company_docs...
  ✅ Created
[2/3] Tạo indexes...
  ✅ department (keyword)
[3/3] Sinh embeddings + upsert 6 documents (3 phòng ban)...
  ✅ 6 points upserted
============================================================
```

---

## BƯỚC 3: Tạo JWT Tokens (3 phòng ban)

> **Lưu ý:** Trên single-node, Qdrant dùng chính API Key (`admin-secret-key-2024`) làm secret để verify JWT.
> Endpoint `/cluster/secret-key` chỉ hoạt động ở cluster mode.

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
D:\Qdrant\.venv\Scripts\python.exe generate_tokens.py
```

Khi script hỏi "Nhập JWT secret key" → nhập: `admin-secret-key-2024`

Script tạo 3 file:
- `token_nhansu.txt` - Filter tự động: `department = NHAN_SU`
- `token_cntt.txt` - Filter tự động: `department = CNTT`
- `token_ketoan.txt` - Filter tự động: `department = KE_TOAN`

---

## BƯỚC 4: Sinh query embeddings

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\generate_query.py
```

Nhập câu hỏi: `Hướng dẫn nghỉ phép`

---

## BƯỚC 5: TEST MULTI-TENANT ISOLATION

### 6.1 Admin → Scroll thấy TẤT CẢ (6 docs, 3 phòng ban) ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/scroll" -H "Content-Type: application/json" -H "api-key: admin-secret-key-2024" -d "{\"limit\":10,\"with_payload\":true}"
```

**Mong đợi:** ✅ 6 documents từ NHAN_SU + CNTT + KE_TOAN.

---

### 6.2 Token Nhân sự → Search (chỉ thấy docs HR) ✅

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
set /p TOKEN_NS=<token_nhansu.txt
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_NS%" -d @..\queries\query_dense.json
```

**Mong đợi:** ✅ Chỉ 2 documents có `department=NHAN_SU`.

---

### 6.3 Token CNTT → Search (chỉ thấy docs IT) ✅

```cmd
set /p TOKEN_IT=<token_cntt.txt
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_IT%" -d @..\queries\query_dense.json
```

**Mong đợi:** ✅ Chỉ 2 documents có `department=CNTT`.

---

### 6.4 Token Kế toán → Search (chỉ thấy docs Kế toán) ✅

```cmd
set /p TOKEN_KT=<token_ketoan.txt
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_KT%" -d @..\queries\query_dense.json
```

**Mong đợi:** ✅ Chỉ 2 documents có `department=KE_TOAN`.

---

### 6.5 Token Nhân sự → Scroll (cố xem hết) → vẫn chỉ thấy HR ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/scroll" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_NS%" -d "{\"limit\":100,\"with_payload\":true}"
```

**Mong đợi:** ✅ Dù limit=100, chỉ thấy 2 docs thuộc NHAN_SU. **Không thể bypass filter.**

---

### 6.6 Token CNTT → Hybrid Search ✅

```cmd
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/query" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_IT%" -d @..\queries\query_hybrid.json
```

**Mong đợi:** ✅ Hybrid search cũng bị filter, chỉ trả docs CNTT.

---

### 6.7 Token CNTT → Upsert doc mới (BỊ TỪ CHỐI do payload restriction) ❌

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
D:\Qdrant\.venv\Scripts\python.exe test_upsert_jwt.py --token-file token_cntt.txt --collection company_docs
```

**Mong đợi:** ❌ 403 Forbidden — Khi token có payload restriction, Qdrant **cấm ghi** để đảm bảo data isolation.

```json
{"status":{"error":"Forbidden: This operation is not allowed when \"payload\" restriction is present for collection company_docs"}}
```

> **Lý do:** Nếu cho phép upsert, user có thể ghi data với department khác rồi bypass filter → mất isolation. Chỉ Admin Key mới được ghi.

---

### 6.8 Admin → Upsert doc CNTT mới, Token Nhân sự vẫn KHÔNG thấy

Admin upsert 1 doc mới thuộc CNTT (dùng script với collection `company_docs`):

```cmd
cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
D:\Qdrant\.venv\Scripts\python.exe test_upsert_admin.py
```

Rồi Token Nhân sự scroll:

```cmd
set /p TOKEN_NS=<token_nhansu.txt
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/scroll" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_NS%" -d "{\"limit\":100,\"with_payload\":true}"
```

**Mong đợi:** ✅ Vẫn chỉ thấy docs NHAN_SU → isolation hoạt động.

---

### 6.9 Token Kế toán → Count (chỉ đếm docs của mình)

```cmd
curl.exe -X POST "http://localhost:6380/collections/company_docs/points/count" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN_KT%" -d "{\"exact\":true}"
```

**Mong đợi:** ✅ `count = 2` (chỉ đếm docs KE_TOAN).

---

## BƯỚC 6: Cleanup

```cmd
curl.exe -X DELETE "http://localhost:6380/collections/company_docs" -H "api-key: admin-secret-key-2024"
cd /d D:\Qdrant\demo-local\auth-demo
docker compose down
```

---

## BẢNG TỔNG KẾT

| Hành động | Token HR | Token IT | Token KT | Admin |
|-----------|----------|----------|----------|-------|
| Search → thấy docs HR | ✅ 2 docs | ❌ 0 | ❌ 0 | ✅ 2 |
| Search → thấy docs IT | ❌ 0 | ✅ 2 docs | ❌ 0 | ✅ 2 |
| Search → thấy docs KT | ❌ 0 | ❌ 0 | ✅ 2 docs | ✅ 2 |
| Scroll toàn bộ | 2 (HR) | 2 (IT) | 2 (KT) | 6 (all) |
| Count | 2 | 2 | 2 | 6 |
| Upsert | ❌ 403 (payload restriction) | ❌ 403 | ❌ 403 | ✅ |
| Delete collection | ❌ | ❌ | ❌ | ✅ |

---

## Ý NGHĨA THỰC TẾ

Kịch bản này mô phỏng hệ thống **RAG multi-tenant**:
- **1 collection** phục vụ nhiều phòng ban/khách hàng
- User đăng nhập → Identity Provider cấp JWT chứa claim `department`
- Qdrant tự filter → user chỉ thấy data "của mình"
- **Không cần tạo nhiều collection** → tiết kiệm tài nguyên
- **Không cần filter thủ công trong app code** → bảo mật ở tầng database
