# BÁO CÁO NGHIÊN CỨU CƠ CHẾ PHÂN QUYỀN QDRANT VECTOR DATABASE

---

**Phiên bản Qdrant:** v1.12.0  
**Ngày nghiên cứu:** Tháng 8/2024  
**Môi trường:** Docker Desktop, Windows, Single Node  

---

## 1. TỔNG QUAN

Qdrant cung cấp **3 cơ chế phân quyền** tăng dần về mức độ chi tiết:

```
┌─────────────────────────────────────────────────────────────┐
│            CƠ CHẾ PHÂN QUYỀN QDRANT                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mức 1: API Key        → Admin vs Read-only vs Anonymous   │
│  Mức 2: JWT per-Collection → Token giới hạn collection     │
│  Mức 3: JWT Payload Filter → Token giới hạn data (rows)    │
│                                                             │
│  Đơn giản ──────────────────────────────────► Phức tạp     │
│  Nhanh deploy                         Multi-tenant SaaS    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. CƠ CHẾ 1: API KEY (Admin vs Read-only)

### 2.1 Nguyên lý

Qdrant hỗ trợ 2 loại API Key cấu hình qua biến môi trường:

```yaml
environment:
  - QDRANT__SERVICE__API_KEY=admin-secret-key-2024          # Full quyền
  - QDRANT__SERVICE__READ_ONLY_API_KEY=readonly-key-2024    # Chỉ đọc
```

### 2.2 Sơ đồ phân quyền

```
                    ┌─────────────┐
                    │   Request   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Có API Key?│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        Không có key   Read-only    Admin key
              │            │            │
              ▼            ▼            ▼
         ❌ 401       ✅ Đọc        ✅ Full
        Unauthorized   ❌ Ghi 403    (Đọc+Ghi+Xóa)
```

### 2.3 Kết quả thực nghiệm

| Thao tác | Anonymous | Read-only Key | Admin Key |
|----------|-----------|---------------|-----------|
| GET /collections | ❌ 401 | ✅ 200 | ✅ 200 |
| POST /points/query (search) | ❌ 401 | ✅ 200 | ✅ 200 |
| POST /points/scroll | ❌ 401 | ✅ 200 | ✅ 200 |
| GET /points/{id} | ❌ 401 | ✅ 200 | ✅ 200 |
| POST /points/count | ❌ 401 | ✅ 200 | ✅ 200 |
| PUT /points (upsert) | ❌ 401 | ❌ 403 | ✅ 200 |
| POST /points/delete | ❌ 401 | ❌ 403 | ✅ 200 |
| PUT /collections (create) | ❌ 401 | ❌ 403 | ✅ 200 |
| DELETE /collections | ❌ 401 | ❌ 403 | ✅ 200 |
| PUT /index (create index) | ❌ 401 | ❌ 403 | ✅ 200 |
| POST /snapshots | ❌ 401 | ❌ 403 | ✅ 200 |

**Kết luận:** API Key chia rõ 3 mức: bị chặn hoàn toàn / chỉ đọc / toàn quyền. Phù hợp khi cần bảo vệ cơ bản (frontend chỉ search, backend mới ghi).

---

## 3. CƠ CHẾ 2: JWT PHÂN QUYỀN THEO COLLECTION

### 3.1 Nguyên lý

Bật `QDRANT__SERVICE__JWT_RBAC=true`, tạo JWT token chứa claim chỉ định collection nào được truy cập:

```json
{
  "exp": 1722000000,
  "access": [
    {"collection": "hr_docs", "access": "rw"}
  ]
}
```

Token được ký bằng API Key (HMAC-SHA256). Qdrant verify chữ ký rồi đọc claim `access`.

### 3.2 Sơ đồ

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Token HR    │     │  Token IT    │     │  Admin Key   │
│ (hr_docs:rw) │     │ (it_docs:rw) │     │  (full)      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────┐         ┌─────────┐         ┌─────────┐
  │ hr_docs │         │ it_docs │         │   ALL   │
  │  ✅ rw  │         │  ✅ rw  │         │  ✅ rw  │
  └─────────┘         └─────────┘         └─────────┘
       │                    │
       ▼                    ▼
  ┌─────────┐         ┌─────────┐
  │ it_docs │         │ hr_docs │
  │  ❌ 403 │         │  ❌ 403 │
  └─────────┘         └─────────┘
```

### 3.3 Kết quả thực nghiệm

| Thao tác | Token HR | Token IT | Admin Key |
|----------|----------|----------|-----------|
| Search hr_docs | ✅ 200 (4 docs) | ❌ 403 | ✅ 200 |
| Search it_docs | ❌ 403 | ✅ 200 (4 docs) | ✅ 200 |
| Upsert hr_docs | ✅ 200 | ❌ 403 | ✅ 200 |
| Upsert it_docs | ❌ 403 | ✅ 200 | ✅ 200 |
| Delete collection | ❌ 403 ("Global access required") | ❌ 403 | ✅ 200 |

**Ví dụ thực tế:**

Token HR search `hr_docs` → trả về 4 documents HR:
```json
{"result":{"points":[
  {"id":1, "payload":{"title":"Quy chế nghỉ phép 2024","department":"NHAN_SU"}},
  {"id":2, "payload":{"title":"Bảng lương tháng 6","department":"NHAN_SU"}},
  {"id":3, "payload":{"title":"Quy trình tuyển dụng","department":"NHAN_SU"}},
  {"id":4, "payload":{"title":"Nội quy công ty","department":"NHAN_SU"}}
]}}
```

Token HR search `it_docs` → bị từ chối:
```json
{"status":{"error":"Forbidden: Access to collection it_docs is required"}}
```

**Kết luận:** Phân quyền theo collection hoạt động chính xác. Mỗi team chỉ truy cập collection được chỉ định trong token.

---

## 4. CƠ CHẾ 3: JWT MULTI-TENANT (Payload Filter)

### 4.1 Nguyên lý

Dùng **1 collection duy nhất** cho nhiều tenant (phòng ban/khách hàng). JWT token chứa claim `payload` filter:

```json
{
  "exp": 1722000000,
  "access": [
    {
      "collection": "company_docs",
      "access": "rw",
      "payload": {"department": "NHAN_SU"}
    }
  ]
}
```

Khi user search/scroll, Qdrant **tự động inject filter** `department = NHAN_SU` → user chỉ thấy data "của mình".

### 4.2 Sơ đồ

```
              ┌─────────────────────────────────────┐
              │       Collection: company_docs       │
              │                                     │
              │  ┌───────┐ ┌───────┐ ┌───────────┐ │
              │  │NHAN_SU│ │ CNTT  │ │  KE_TOAN  │ │
              │  │ 2 docs│ │2 docs │ │  2 docs   │ │
              │  └───┬───┘ └───┬───┘ └─────┬─────┘ │
              └──────┼─────────┼───────────┼───────┘
                     │         │           │
         ┌───────────┤         │           ├───────────┐
         │           │         │           │           │
    Token HR    Token IT  Token KT    Admin Key
    (filter:    (filter:  (filter:    (no filter)
    NHAN_SU)    CNTT)     KE_TOAN)
         │           │         │           │
         ▼           ▼         ▼           ▼
    Thấy 2 docs Thấy 2 docs Thấy 2 docs Thấy 6 docs
    (chỉ HR)   (chỉ IT)   (chỉ KT)   (tất cả)
```

### 4.3 Kết quả thực nghiệm

| Thao tác | Token HR | Token IT | Token KT | Admin |
|----------|----------|----------|----------|-------|
| Search | 2 docs (NHAN_SU) | 2 docs (CNTT) | 2 docs (KE_TOAN) | 6 docs (all) |
| Scroll limit=100 | 2 docs | 2 docs | 2 docs | 6 docs |
| Hybrid search | 2 docs (filtered) | 2 docs (filtered) | 2 docs (filtered) | 6 docs |
| Count | 2 | 2 | 2 | 6 |
| Upsert | ❌ 403 | ❌ 403 | ❌ 403 | ✅ 200 |

**Ví dụ thực tế:**

Token Nhân sự search → chỉ thấy 2 docs NHAN_SU:
```json
{"result":{"points":[
  {"id":1, "score":0.81, "payload":{"title":"Quy chế nghỉ phép 2024","department":"NHAN_SU"}},
  {"id":2, "score":0.74, "payload":{"title":"Bảng lương tháng 6","department":"NHAN_SU"}}
]}}
```

Token CNTT hybrid search → chỉ thấy 2 docs CNTT:
```json
{"result":{"points":[
  {"id":3, "score":0.83, "payload":{"title":"Hướng dẫn cài đặt VPN","department":"CNTT"}},
  {"id":4, "score":0.83, "payload":{"title":"Chính sách bảo mật password","department":"CNTT"}}
]}}
```

Token Kế toán count → chỉ đếm được 2:
```json
{"result":{"count":2}}
```

### 4.4 Đặc điểm quan trọng phát hiện

**Khi token có payload restriction, Qdrant CẤM upsert:**

```json
{"status":{"error":"Forbidden: This operation is not allowed when \"payload\" restriction is present for collection company_docs"}}
```

**Lý do:** Nếu cho phép user ghi, họ có thể tạo document với `department` khác → bypass filter → phá vỡ isolation. Chỉ Admin mới được ghi data.

**Không thể bypass filter:** Dù scroll với `limit=100`, token vẫn chỉ thấy data thuộc department của mình.

**Admin upsert doc mới thuộc CNTT → Token NHAN_SU vẫn không thấy:** Isolation giữa các tenant được đảm bảo.

---

## 5. SO SÁNH 3 CƠ CHẾ

| Tiêu chí | API Key | JWT per-Collection | JWT Payload Filter |
|----------|---------|-------------------|-------------------|
| Độ phức tạp | ⭐ Thấp | ⭐⭐ Trung bình | ⭐⭐⭐ Cao |
| Granularity | Toàn bộ DB | Theo collection | Theo row (data) |
| Số collection cần | 1 | N (mỗi team 1) | 1 (dùng chung) |
| Token expiry | Không | Có (exp claim) | Có (exp claim) |
| Ghi data | Admin: ✅ / RO: ❌ | Token rw: ✅ | ❌ (chỉ Admin) |
| Use case | Frontend search | Team riêng collection | Multi-tenant SaaS |
| Setup | Chỉ env var | Env + script Python | Env + script + index |

---

## 6. SƠ ĐỒ KIẾN TRÚC TỔNG THỂ

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌──────────────┐  │
│  │ App FE  │   │ Team HR │   │ Team IT │   │ Admin/CI-CD  │  │
│  │(RO key) │   │(JWT HR) │   │(JWT IT) │   │(Admin key)   │  │
│  └────┬────┘   └────┬────┘   └────┬────┘   └──────┬───────┘  │
│       │              │              │               │          │
└───────┼──────────────┼──────────────┼───────────────┼──────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QDRANT AUTH LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Verify key/token (HMAC-SHA256)                              │
│  2. Check exp (token hết hạn?)                                  │
│  3. Check collection access                                     │
│  4. Apply payload filter (nếu có)                               │
│  5. Check read/write permission                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QDRANT DATA LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Collection: smart_search  │  Collection: hr_docs  │ it_docs   │
│  ┌────────────────────┐    │  ┌──────────────┐    ┌────────┐  │
│  │ Points (vectors +  │    │  │ Points (HR)  │    │ Points │  │
│  │ payload metadata)  │    │  │              │    │ (IT)   │  │
│  └────────────────────┘    │  └──────────────┘    └────────┘  │
│                            │                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. KHUYẾN NGHỊ SỬ DỤNG

| Tình huống | Cơ chế phù hợp |
|-----------|----------------|
| API public cho frontend search | Read-only API Key |
| Backend admin quản lý data | Admin API Key |
| Nhiều team, mỗi team 1 knowledge base | JWT per-Collection |
| 1 knowledge base, nhiều phòng ban | JWT Payload Filter |
| SaaS multi-tenant (nhiều khách hàng) | JWT Payload Filter |
| CI/CD pipeline cần ghi data | Admin API Key |

---

## 8. HẠN CHẾ PHÁT HIỆN

1. **JWT Payload Filter cấm upsert:** Khi token có payload restriction, user không thể ghi data. Chỉ Admin key mới ghi được → cần thiết kế ingestion pipeline riêng.

2. **Token expiry:** JWT token có hạn (exp claim). Cần cơ chế refresh token nếu dùng trong ứng dụng dài hạn.

3. **Secret key = API Key:** Trên single node, Qdrant dùng chính API Key làm JWT signing secret. Nếu lộ API Key thì attacker có thể tự tạo JWT token bất kỳ.

4. **Không có endpoint lấy secret trên single node:** `/cluster/secret-key` chỉ hoạt động ở cluster mode.

5. **InsecureKeyLengthWarning:** API Key ngắn hơn 32 bytes sẽ bị cảnh báo khi ký JWT (RFC 7518). Khuyến nghị dùng key dài hơn trong production.

---

## 9. KẾT LUẬN

Qdrant cung cấp hệ thống phân quyền đầy đủ từ cơ bản (API Key) đến nâng cao (JWT multi-tenant). Qua thực nghiệm:

- **API Key:** Hoạt động chính xác, chia rõ 3 mức quyền (401/403/200)
- **JWT per-Collection:** Cô lập hoàn toàn giữa các collection, phù hợp tổ chức theo team
- **JWT Payload Filter:** Cô lập data trong cùng 1 collection, không thể bypass bằng bất kỳ cách nào (scroll, limit lớn, hybrid search)

Hệ thống phân quyền Qdrant đủ mạnh để triển khai trong môi trường production, đặc biệt phù hợp cho các hệ thống RAG multi-tenant nơi nhiều phòng ban/khách hàng cùng dùng chung 1 vector database.
