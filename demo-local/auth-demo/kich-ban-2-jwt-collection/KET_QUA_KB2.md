# KẾT QUẢ KỊCH BẢN 2: JWT PHÂN QUYỀN THEO COLLECTION

> Ngày chạy: ___/___/2024
> Người thực hiện: _______________
> Phiên bản Qdrant: v1.12.0

---

## Setup

```
docker compose ps:

```
[+] Running 2/2
 ✔ Network auth-demo_default   Created                                                                             0.1s
 ✔ Container qdrant-auth-demo  Started                                                                             0.8s

D:\Qdrant\demo-local\auth-demo>docker compose ps
NAME               IMAGE                   COMMAND             SERVICE       CREATED                  STATUS                  PORTS
qdrant-auth-demo   qdrant/qdrant:v1.12.0   "./entrypoint.sh"   qdrant-auth   Less than a second ago   Up Less than a second   0.0.0.0:6380->6333/tcp, [::]:6380->6333/tcp, 0.0.0.0:6381->6334/tcp, [::]:6381->6334/tcp
---

## Bước 2: Lấy JWT Secret

```
Lệnh: curl.exe -X GET "http://localhost:6380/cluster/secret-key" -H "api-key: admin-secret-key-2024"
Kết quả (secret key):

```

---

## Bước 3: Tạo JWT Tokens (generate_tokens.py)

```
Output:
✅ Đã tạo token thành công!
   - token_hr.txt (quyền: hr_docs, rw)
   - token_it.txt (quyền: it_docs, rw)

📋 Token HR: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3O...
📋 Token IT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3O...
```

---

## Bước 4: Setup data (setup_data.py)

```
Output:

SETUP DATA CHO KỊCH BẢN 2: JWT PER-COLLECTION
============================================================

[*] Tạo indexes cho hr_docs...

[*] Tạo indexes cho it_docs...

[1/2] Collection hr_docs...

  Sinh embeddings cho 4 documents...
  ✅ Upserted 4 points vào hr_docs

[2/2] Collection it_docs...

  Sinh embeddings cho 4 documents...
  ✅ Upserted 4 points vào it_docs

============================================================
  ✅ hr_docs: 4 points
  ✅ it_docs: 4 points
============================================================
```

---

## Bước 5: Sinh query (generate_query.py)

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

```

---

## Bước 6: Test phân quyền JWT

### 6.1 Token HR → Search hr_docs (phải thành công)

```
Kết quả:
{"result":{"points":[{"id":1,"version":2,"score":0.8115994,"payload":{"title":"Quy chế nghỉ phép 2024","text":"Nhân viên được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.","department":"NHAN_SU"}},{"id":2,"version":2,"score":0.74532795,"payload":{"title":"Bảng lương tháng 6","text":"Lương cơ bản + phụ cấp ăn trưa + thưởng KPI. Chuyển khoản trước ngày 5.","department":"NHAN_SU"}},{"id":3,"version":2,"score":0.71769565,"payload":{"title":"Quy trình tuyển dụng","text":"Nhận CV → phỏng vấn vòng 1 → test kỹ thuật → phỏng vấn vòng 2 → offer.","department":"NHAN_SU"}},{"id":4,"version":2,"score":0.7132673,"payload":{"title":"Nội quy công ty","text":"Giờ làm việc 8h-17h. Đi trễ 3 lần bị cảnh cáo. Trang phục lịch sự.","department":"NHAN_SU"}}]},"status":"ok","time":0.003443866}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.2 Token HR → Search it_docs (phải bị 403)

```
Kết quả:
{"status":{"error":"Forbidden: Access to collection it_docs is required"},"time":0.000021455}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.3 Token IT → Search it_docs (phải thành công)

```
Kết quả:
{"result":{"points":[{"id":2,"version":2,"score":0.70641077,"payload":{"title":"Chính sách bảo mật","text":"Password tối thiểu 12 ký tự, đổi mỗi 90 ngày. Bật 2FA cho email.","department":"CNTT"}},{"id":1,"version":2,"score":0.6560879,"payload":{"title":"Hướng dẫn cài đặt VPN","text":"Tải OpenVPN client, import file .ovpn từ IT. Kết nối bằng tài khoản AD.","department":"CNTT"}},{"id":3,"version":2,"score":0.59397054,"payload":{"title":"Hướng dẫn Git workflow","text":"Dùng feature branch → pull request → code review → merge vào main.","department":"CNTT"}},{"id":4,"version":2,"score":0.53526354,"payload":{"title":"Cấu hình CI/CD pipeline","text":"Push code → GitHub Actions build → test → deploy staging → deploy prod.","department":"CNTT"}}]},"status":"ok","time":0.001713838}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.4 Token IT → Search hr_docs (phải bị 403)

```
Kết quả:
{"status":{"error":"Forbidden: Access to collection hr_docs is required"},"time":0.000020723}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.5 Token HR → Upsert hr_docs (phải thành công)

```
Kết quả:
✅ HTTP 200 - Upsert vào hr_docs thành công
{
  "result": {
    "operation_id": 3,
    "status": "completed"
  },
  "status": "ok",
  "time": 0.047340219
}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.6 Token IT → Upsert hr_docs (phải bị 403)

```
Kết quả:
❌ HTTP 403 - Upsert vào hr_docs bị từ chối
{"status":{"error":"Forbidden: Access to collection hr_docs is required"},"time":0.00014025}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### 6.7 Token HR → Delete collection (phải bị 403)

```
Kết quả:
{"status":{"error":"Forbidden: Global access is required"},"time":9.966e-6}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

## Tổng kết

| # | Test case | Mong đợi | Thực tế | Pass? |
|---|-----------|----------|---------|-------|
| 6.1 | Token HR → Search hr_docs | 200 | | ☐ |
| 6.2 | Token HR → Search it_docs | 403 | | ☐ |
| 6.3 | Token IT → Search it_docs | 200 | | ☐ |
| 6.4 | Token IT → Search hr_docs | 403 | | ☐ |
| 6.5 | Token HR → Upsert hr_docs | 200 | | ☐ |
| 6.6 | Token IT → Upsert hr_docs | 403 | | ☐ |
| 6.7 | Token HR → Delete collection | 403 | | ☐ |

**Tổng: ___/7 passed**

---

## Ghi chú / Vấn đề phát sinh

```

```
