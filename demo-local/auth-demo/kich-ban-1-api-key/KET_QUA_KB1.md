# KẾT QUẢ KỊCH BẢN 1: SO SÁNH 3 ROLE (Anonymous vs Read-only vs Admin)

> Ngày chạy: ___/___/2024
> Người thực hiện: _______________
> Phiên bản Qdrant: v1.12.0

---

## Setup

```
docker compose ps:
NAME               IMAGE                   COMMAND             SERVICE       CREATED          STATUS          PORTS
qdrant-auth-demo   qdrant/qdrant:v1.12.0   "./entrypoint.sh"   qdrant-auth   20 seconds ago   Up 21 seconds   0.0.0.0:6380->6333/tcp, [::]:6380->6333/tcp, 0.0.0.0:6381->6334/tcp, [::]:6381->6334/tcp

setup_collection.py output:
SETUP COLLECTION CHO AUTH DEMO
============================================================

[1/4] Xóa collection cũ (nếu tồn tại)...
  ✅ Done

[2/4] Tạo collection 'auth_demo'...
  ✅ Collection created

[3/4] Tạo payload indexes...
  ✅ Index: doc_status
  ✅ Index: domain
  ✅ Index: department
  ✅ Index: doc_type

[4/4] Upsert data từ sample_data...
  ✅ points_batch_01.json: 6 points
  ✅ points_batch_02.json: 6 points

============================================================
✅ HOÀN TẤT! Collection 'auth_demo' có 12 points.
============================================================
generate_query.py:
  Câu hỏi: Hướng dẫn nghỉ phép
`
[1/2] Sinh Hybrid Search body (dense + sparse + RRF)...
  ✅ Saved: query_hybrid.json
[2/2] Sinh Dense Search body...
  ✅ Saved: query_dense.json

==================================================
✅ Đã lưu 2 file query vào: D:\Qdrant\demo-local\auth-demo\queries
   - query_hybrid.json (hybrid search)
   - query_dense.json  (dense only)

Câu hỏi: 'Hướng dẫn nghỉ phép'
---

## ANONYMOUS (No Key)

### 4.1 Anonymous → Đọc collections

```
Kết quả:
Must provide an API key or an Authorization bearer token
```

| Đúng mong đợi? (401) | ☐ Có | ☐ Không |

---

### 4.2 Anonymous → Search

```
Kết quả:
Must provide an API key or an Authorization bearer token

```

| Đúng mong đợi? (401) | ☐ Có | ☐ Không |

---

## ADMIN KEY

### 5.1 Admin → Đọc collections

```
Kết quả:
{"result":{"collections":[{"name":"auth_demo"}]},"status":"ok","time":8.904e-6}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

### 5.2 Admin → Search

```
Kết quả:
{"result":{"points":[{"id":1,"version":8,"score":0.8567471,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."}},{"id":2,"version":8,"score":0.7655409,"payload":{"document_id":"DOC-002","title":"Làm thêm giờ","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Làm thêm giờ phải được trưởng bộ phận phê duyệt trước khi thực hiện."}},{"id":10,"version":9,"score":0.7357621,"payload":{"document_id":"DOC-010","title":"Hồ sơ nhân sự","domain":"nhan_su","department":"BAN_LE","doc_type":"mau","doc_status":"ACTIVE","text":"Hồ sơ nhân sự phải được lưu trữ theo quy định bảo mật và cập nhật hàng quý."}},{"id":3,"version":8,"score":0.73320013,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}},{"id":11,"version":9,"score":0.73066705,"payload":{"document_id":"DOC-011","title":"Công nghệ AI trong nội bộ","domain":"cong_nghe","department":"IT","doc_type":"thong_tin","doc_status":"ACTIVE","text":"Các giải pháp AI nội bộ được giới hạn cho việc tối ưu quy trình và không thay thế quyết định của con người."}}]},"status":"ok","time":0.001999846}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

### 5.3 Admin → Upsert

```
Kết quả:
✅ HTTP 200
{
  "result": {
    "operation_id": 11,
    "status": "completed"
  },
  "status": "ok",
  "time": 0.007210842
}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

### 5.4 Admin → Xóa point

```
Kết quả:
{"result":{"operation_id":12,"status":"acknowledged"},"status":"ok","time":0.001221043}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

## READ-ONLY KEY

### 6.1 Read-only → Đọc collections

```
Kết quả:
{"result":{"collections":[{"name":"auth_demo"}]},"status":"ok","time":6.829e-6}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

### 6.2 Read-only → Search

```
Kết quả:
{"result":{"points":[{"id":1,"version":8,"score":0.8567471,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."}},{"id":2,"version":8,"score":0.7655409,"payload":{"document_id":"DOC-002","title":"Làm thêm giờ","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Làm thêm giờ phải được trưởng bộ phận phê duyệt trước khi thực hiện."}},{"id":10,"version":9,"score":0.7357621,"payload":{"document_id":"DOC-010","title":"Hồ sơ nhân sự","domain":"nhan_su","department":"BAN_LE","doc_type":"mau","doc_status":"ACTIVE","text":"Hồ sơ nhân sự phải được lưu trữ theo quy định bảo mật và cập nhật hàng quý."}},{"id":3,"version":8,"score":0.73320013,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}},{"id":11,"version":9,"score":0.73066705,"payload":{"document_id":"DOC-011","title":"Công nghệ AI trong nội bộ","domain":"cong_nghe","department":"IT","doc_type":"thong_tin","doc_status":"ACTIVE","text":"Các giải pháp AI nội bộ được giới hạn cho việc tối ưu quy trình và không thay thế quyết định của con người."}}]},"status":"ok","time":0.002836959}
```

| Đúng mong đợi? (200) | ☐ Có | ☐ Không |

---

### 6.3 Read-only → Upsert (phải bị 403)

```
Kết quả:
❌ HTTP 403
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000013029}
```

| Đúng mong đợi? (403) | ☐ Có | ☐ Không |

---

### 6.4 Read-only → Xóa collection (phải bị 403)

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":8.178e-6}
```

| Đúng mong đợi? (403) | ☐ Có | ☐ Không |

---

## Tổng kết

| # | Test case | Role | Mong đợi | Thực tế | Pass? |
|---|-----------|------|----------|---------|-------|
| 4.1 | Đọc collections | Anonymous | 401 | | ☐ |
| 4.2 | Search | Anonymous | 401 | | ☐ |
| 5.1 | Đọc collections | Admin | 200 | | ☐ |
| 5.2 | Search | Admin | 200 | | ☐ |
| 5.3 | Upsert | Admin | 200 | | ☐ |
| 5.4 | Delete point | Admin | 200 | | ☐ |
| 6.1 | Đọc collections | Read-only | 200 | | ☐ |
| 6.2 | Search | Read-only | 200 | | ☐ |
| 6.3 | Upsert | Read-only | 403 | | ☐ |
| 6.4 | Delete collection | Read-only | 403 | | ☐ |

**Tổng: ___/10 passed**

---

## Ghi chú / Vấn đề phát sinh

```

```
