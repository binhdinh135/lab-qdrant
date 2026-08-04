# KẾT QUẢ KỊCH BẢN 3: JWT MULTI-TENANT (Payload Filter)

> Ngày chạy: ___/___/2024
> Người thực hiện: _______________
> Phiên bản Qdrant: v1.12.0

---

## Setup

```
docker compose ps:

```
[+] Running 1/1
 ✔ Container qdrant-auth-demo  Running                                                                             0.0s

D:\Qdrant\demo-local\auth-demo>docker compose ps
NAME               IMAGE                   COMMAND             SERVICE       CREATED          STATUS          PORTS
qdrant-auth-demo   qdrant/qdrant:v1.12.0   "./entrypoint.sh"   qdrant-auth   24 seconds ago   Up 24 seconds   0.0.0.0:6380->6333/tcp, [::]:6380->6333/tcp, 0.0.0.0:6381->6334/tcp, [::]:6381->6334/tcp

---

## Bước 2: Setup data (setup_data.py)

```
Output:
SETUP DATA CHO KỊCH BẢN 3: MULTI-TENANT
============================================================

[1/3] Tạo collection company_docs...
  ✅ Created

[2/3] Tạo indexes...
  ✅ department (keyword)

[3/3] Sinh embeddings + upsert 6 documents (3 phòng ban)...
  ✅ 6 points upserted

============================================================
✅ HOÀN TẤT! Collection 'company_docs' có 6 points (3 phòng ban).
============================================================
Số points: 
Phòng ban: NHAN_SU (2), CNTT (2), KE_TOAN (2)
```

---

## Bước 3: Tạo JWT Tokens (generate_tokens.py)

> Secret key nhập: admin-secret-key-2024

```
Output:

✅ Đã tạo 3 token thành công!
   - token_nhansu.txt  (filter: department=NHAN_SU)
   - token_cntt.txt    (filter: department=CNTT)
   - token_ketoan.txt  (filter: department=KE_TOAN)

📋 Token Nhân sự: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3O...
📋 Token CNTT:    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3O...
📋 Token Kế toán: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3O...

```

---

## Bước 4: Sinh query (generate_query.py)

```
Câu hỏi: 
```
Nhập câu hỏi tiếng Việt: Hướng dẫn nghỉ phép

[1/2] Sinh Hybrid Search body (dense + sparse + RRF)...
  ✅ Saved: query_hybrid.json
[2/2] Sinh Dense Search body...
  ✅ Saved: query_dense.json

==================================================
✅ Đã lưu 2 file query vào: D:\Qdrant\demo-local\auth-demo\queries
   - query_hybrid.json (hybrid search)
   - query_dense.json  (dense only)

Câu hỏi: 'Hướng dẫn nghỉ phép'
==================================================
---

## Bước 5: Test Multi-tenant Isolation

### 6.1 Admin → Scroll thấy TẤT CẢ (6 docs)

```
Kết quả:

{"result":{"points":[{"id":1,"payload":{"title":"Quy chế nghỉ phép 2024","text":"Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.","department":"NHAN_SU"}},{"id":2,"payload":{"title":"Bảng lương tháng 6","text":"Lương cơ bản + phụ cấp ăn trưa + thưởng KPI hàng quý. Chuyển khoản trước ngày 5.","department":"NHAN_SU"}},{"id":3,"payload":{"title":"Hướng dẫn cài đặt VPN","text":"Tải OpenVPN client từ share drive. Import file .ovpn. Kết nối bằng tài khoản Active Directory.","department":"CNTT"}},{"id":4,"payload":{"title":"Chính sách bảo mật password","text":"Password tối thiểu 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt. Đổi mỗi 90 ngày.","department":"CNTT"}},{"id":5,"payload":{"title":"Quy trình đề nghị thanh toán","text":"Điền form đề nghị thanh toán trước ngày 25. Đính kèm hóa đơn gốc. Trưởng phòng ký duyệt.","department":"KE_TOAN"}},{"id":6,"payload":{"title":"Báo cáo tài chính Q2 2024","text":"Doanh thu tăng 15% so với Q1. Chi phí vận hành giảm 5%. Lợi nhuận ròng đạt mục tiêu.","department":"KE_TOAN"}}],"next_page_offset":null},"status":"ok","time":0.006080801}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.2 Token Nhân sự → Search (chỉ thấy HR)

```
Kết quả:
{"result":{"points":[{"id":1,"version":2,"score":0.8105338,"payload":{"title":"Quy chế nghỉ phép 2024","text":"Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.","department":"NHAN_SU"}},{"id":2,"version":2,"score":0.74766433,"payload":{"title":"Bảng lương tháng 6","text":"Lương cơ bản + phụ cấp ăn trưa + thưởng KPI hàng quý. Chuyển khoản trước ngày 5.","department":"NHAN_SU"}}]},"status":"ok","time":0.007250587}
Số docs thấy: ___
Titles: 
```

| Đúng mong đợi? (chỉ NHAN_SU) | ☐ Có | ☐ Không |

---

### 6.3 Token CNTT → Search (chỉ thấy IT)

```
Kết quả:
{"result":{"points":[{"id":4,"version":2,"score":0.66359174,"payload":{"title":"Chính sách bảo mật password","text":"Password tối thiểu 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt. Đổi mỗi 90 ngày.","department":"CNTT"}},{"id":3,"version":2,"score":0.6347724,"payload":{"title":"Hướng dẫn cài đặt VPN","text":"Tải OpenVPN client từ share drive. Import file .ovpn. Kết nối bằng tài khoản Active Directory.","department":"CNTT"}}]},"status":"ok","time":0.000812288}
Số docs thấy: ___
Titles: 
```

| Đúng mong đợi? (chỉ CNTT) | ☐ Có | ☐ Không |

---

### 6.4 Token Kế toán → Search (chỉ thấy KT)

```
Kết quả:
{"result":{"points":[{"id":5,"version":2,"score":0.74560916,"payload":{"title":"Quy trình đề nghị thanh toán","text":"Điền form đề nghị thanh toán trước ngày 25. Đính kèm hóa đơn gốc. Trưởng phòng ký duyệt.","department":"KE_TOAN"}},{"id":6,"version":2,"score":0.7004651,"payload":{"title":"Báo cáo tài chính Q2 2024","text":"Doanh thu tăng 15% so với Q1. Chi phí vận hành giảm 5%. Lợi nhuận ròng đạt mục tiêu.","department":"KE_TOAN"}}]},"status":"ok","time":0.001270652}
Số docs thấy: ___
Titles: 
```

| Đúng mong đợi? (chỉ KE_TOAN) | ☐ Có | ☐ Không |

---

### 6.5 Token Nhân sự → Scroll limit=100 (vẫn chỉ HR)

```
Kết quả:
{"result":{"points":[{"id":1,"payload":{"title":"Quy chế nghỉ phép 2024","text":"Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.","department":"NHAN_SU"}},{"id":2,"payload":{"title":"Bảng lương tháng 6","text":"Lương cơ bản + phụ cấp ăn trưa + thưởng KPI hàng quý. Chuyển khoản trước ngày 5.","department":"NHAN_SU"}}],"next_page_offset":null},"status":"ok","time":0.000809223}
Số docs thấy: ___
```

| Bypass được filter không? | ☐ Không (đúng) | ☐ Có (LỖI!) |

---

### 6.6 Token CNTT → Hybrid Search

```
Kết quả:
{"result":{"points":[{"id":3,"version":2,"score":0.8333334,"payload":{"title":"Hướng dẫn cài đặt VPN","text":"Tải OpenVPN client từ share drive. Import file .ovpn. Kết nối bằng tài khoản Active Directory.","department":"CNTT"}},{"id":4,"version":2,"score":0.8333334,"payload":{"title":"Chính sách bảo mật password","text":"Password tối thiểu 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt. Đổi mỗi 90 ngày.","department":"CNTT"}}]},"status":"ok","time":0.001865119}
Số docs thấy: ___
Tất cả đều CNTT?: 
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.7 Token CNTT → Upsert doc mới

```
Kết quả:
❌ HTTP 403 - Upsert bị từ chối
{"status":{"error":"Forbidden: This operation is not allowed when \"payload\" restriction is present for collection company_docs"},"time":9.047e-6}

```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.8 Token Nhân sự → Scroll (không thấy doc mới của CNTT)
✅ HTTP 200 - Admin upsert doc CNTT vào company_docs
{
  "result": {
    "operation_id": 3,
    "status": "completed"
  },
  "status": "ok",
  "time": 0.012426011
}

```
Kết quả:

{"result":{"points":[{"id":1,"payload":{"title":"Quy chế nghỉ phép 2024","text":"Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.","department":"NHAN_SU"}},{"id":2,"payload":{"title":"Bảng lương tháng 6","text":"Lương cơ bản + phụ cấp ăn trưa + thưởng KPI hàng quý. Chuyển khoản trước ngày 5.","department":"NHAN_SU"}}],"next_page_offset":null},"status":"ok","time":0.00106292}
Số docs thấy: ___
Có thấy doc CNTT mới không?: 
```

| Isolation hoạt động? | ☐ Có | ☐ Không |

---

### 6.9 Token Kế toán → Count

```
Kết quả:
{"result":{"count":2},"status":"ok","time":0.00075444}
Count: ___
```

| Đúng mong đợi? (count = 2) | ☐ Có | ☐ Không |

---

## Tổng kết

| # | Test case | Mong đợi | Thực tế | Pass? |
|---|-----------|----------|---------|-------|
| 6.1 | Admin scroll | 6 docs (3 phòng ban) | | ☐ |
| 6.2 | Token HR → search | Chỉ 2 docs NHAN_SU | | ☐ |
| 6.3 | Token IT → search | Chỉ 2 docs CNTT | | ☐ |
| 6.4 | Token KT → search | Chỉ 2 docs KE_TOAN | | ☐ |
| 6.5 | Token HR → scroll limit=100 | Vẫn chỉ 2 docs HR | | ☐ |
| 6.6 | Token IT → hybrid search | Chỉ docs CNTT | | ☐ |
| 6.7 | Token IT → upsert | 200 OK | | ☐ |
| 6.8 | Token HR → không thấy doc IT mới | Isolation OK | | ☐ |
| 6.9 | Token KT → count | count = 2 | | ☐ |

**Tổng: ___/9 passed**

---

## Kết luận Multi-tenant

| Tiêu chí | Đạt? |
|-----------|------|
| Mỗi token chỉ thấy data của phòng mình | ☐ |
| Không thể bypass filter bằng scroll/limit lớn | ☐ |
| Hybrid search cũng bị filter | ☐ |
| Upsert hoạt động bình thường | ☐ |
| Data mới của phòng A không lộ sang phòng B | ☐ |

---

## Ghi chú / Vấn đề phát sinh

```

```
