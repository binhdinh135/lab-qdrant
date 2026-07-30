# BÁO CÁO KẾT QUẢ DEMO QDRANT TRÊN MÁY CÁ NHÂN

| Thông tin | Giá trị |
|-----------|---------|
| Ngày thực hiện | 29/07/2026 |
| Mục tiêu | Demo triển khai Qdrant local, test CRUD + Search + Filter |
| Phiên bản Qdrant | v1.12.0 |
| Phương thức | Docker + PowerShell (REST API) |
| Kết quả tổng quan | **PASS – Toàn bộ 12 bước chạy thành công** |

---

## 1. CẤU HÌNH MÁY DEMO

| Thông số | Giá trị |
|----------|---------|
| CPU | Intel i7-1165G7 @ 2.80GHz (4 cores / 8 threads) |
| RAM | 16 GB DDR4 3200MHz |
| Ổ cứng | D: 293 GB (trống 155 GB) |
| OS | Windows 11 Home |
| Docker | Docker Desktop v29.1.3 |
| Giới hạn container | 2 GB RAM, 2 CPU cores |

**Nhận xét:** Máy hoạt động bình thường trong suốt quá trình demo, không lag, không treo.

---

## 2. CẤU HÌNH QDRANT DEMO

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| Collection | smart_search_demo | |
| Vector size | 384 dimensions | Giả lập (production sẽ dùng 1024d BGE-M3) |
| Distance | Cosine | |
| Shard | 1 | Local không cần chia shard |
| Replica | 1 | Local không cần HA |
| Payload indexes | 4 (doc_status, domain, department, doc_type) | Keyword type |
| Số points | 12 (2 batches × 6) | |

---

## 3. KẾT QUẢ TỪNG BƯỚC

### 3.1 Khởi động & Kết nối

| Bước | Lệnh | Kết quả | Thời gian |
|------|-------|---------|-----------|
| Start container | `docker compose up -d` | ✅ Container started | 0.4s |
| Health check | `GET /healthz` | ✅ "healthz check passed" | — |
| Version check | `GET /` | ✅ Qdrant v1.12.0 | — |

### 3.2 Tạo Collection & Indexes

| Bước | Kết quả | Thời gian |
|------|---------|-----------|
| Tạo collection | ✅ status: ok | 348ms |
| Index: doc_status | ✅ acknowledged | 16ms |
| Index: domain | ✅ acknowledged | 12ms |
| Index: department | ✅ acknowledged | 14ms |
| Index: doc_type | ✅ acknowledged | 13ms |

### 3.3 Upsert dữ liệu

| Batch | Nội dung | Kết quả | Thời gian |
|-------|----------|---------|-----------|
| Batch 01 | 6 points (domain: nhan_su) | ✅ completed | 30ms |
| Batch 02 | 6 points (domain: cong_nghe, hanh_chinh) | ✅ completed | 20ms |
| **Tổng** | **12 points** | ✅ points_count = 12 | **50ms** |

### 3.4 Search (Vector Similarity)

#### Search cơ bản (không filter)

| # | Score | Doc ID | Title | Domain |
|---|-------|--------|-------|--------|
| 1 | 0.1200 | DOC-009 | Quy trinh deploy Production | cong_nghe |
| 2 | 0.0888 | DOC-010 | Quy dinh su dung VPN | cong_nghe |
| 3 | 0.0703 | DOC-001 | Quy dinh nghi phep nam 2024 | nhan_su |
| 4 | 0.0685 | DOC-001 | Quy dinh nghi phep nam 2024 | nhan_su |
| 5 | 0.0468 | DOC-004 | Quy dinh danh gia KPI | nhan_su |

⏱️ Thời gian: **2.2ms**

#### Search + Filter: domain = cong_nghe

| # | Score | Doc ID | Title |
|---|-------|--------|-------|
| 1 | 0.1398 | DOC-008 | Huong dan su dung eISO |
| 2 | 0.0492 | DOC-010 | Quy dinh su dung VPN |
| 3 | 0.0441 | DOC-009 | Quy trinh deploy Production |
| 4 | -0.0115 | DOC-006 | Chinh sach bao mat thong tin |
| 5 | -0.0689 | DOC-007 | Quy trinh xu ly su co he thong |

⏱️ Thời gian: **1.6ms** | ✅ Chỉ trả về domain=cong_nghe

#### Search + Filter: department = NHAN_SU

| # | Score | Doc ID | Title |
|---|-------|--------|-------|
| 1 | 0.0188 | DOC-002 | Quy trinh tuyen dung nhan su |

⏱️ Thời gian: **1.2ms** | ✅ Chỉ trả về department=NHAN_SU (đúng 1 point)

#### Search + Multi-filter: domain=cong_nghe AND doc_type=quy_trinh AND doc_status=ACTIVE

| # | Score | Doc ID | Title |
|---|-------|--------|-------|
| 1 | 0.0335 | DOC-009 | Quy trinh deploy Production |
| 2 | -0.0037 | DOC-007 | Quy trinh xu ly su co he thong |

⏱️ Thời gian: **1.1ms** | ✅ Filter kết hợp 3 điều kiện hoạt động chính xác

### 3.5 Scroll (Liệt kê dữ liệu)

| Kết quả | Chi tiết |
|---------|----------|
| Trả về 5 points | id: 1, 2, 3, 4, 5 |
| next_page_offset | 6 (pagination hoạt động) |
| Thời gian | 1.1ms |

### 3.6 Update Payload

| Thao tác | Points | Kết quả |
|----------|--------|---------|
| Đổi doc_status → "ARCHIVED" | 1, 2, 3 | ✅ acknowledged |

→ Sau update, search filter `doc_status=ACTIVE` sẽ không trả về points 1, 2, 3.

### 3.7 Delete Points

| Thao tác | Points | Kết quả |
|----------|--------|---------|
| Xóa points | 1, 2, 3 | ✅ acknowledged |

### 3.8 Snapshot (Backup)

| Thông tin | Giá trị |
|-----------|---------|
| Tên file | smart_search_demo-2848121824292700-2026-07-29-07-41-28.snapshot |
| Thời gian tạo | 2026-07-29T07:41:34 |
| Kích thước | ~136 MB |
| Checksum | 5aaa069c21a30d789ac7eb135934f0a95374933eb2bbd7f556bd3bb7090a2dad |

### 3.9 Cleanup

| Thao tác | Kết quả |
|----------|---------|
| Xóa collection | ✅ result: True (32ms) |

---

## 4. TỔNG HỢP HIỆU NĂNG

| Thao tác | Latency | Đánh giá |
|----------|---------|----------|
| Tạo collection | 348ms | Tốt (chỉ chạy 1 lần) |
| Tạo index | 12-16ms | Rất nhanh |
| Upsert (6 points/batch) | 20-30ms | Rất nhanh |
| Search (không filter) | 2.2ms | Xuất sắc |
| Search + 1 filter | 1.2-1.6ms | Xuất sắc |
| Search + multi-filter | 1.1ms | Xuất sắc |
| Scroll | 1.1ms | Xuất sắc |
| Snapshot | ~6s | Chấp nhận được |

**Nhận xét:** Latency search đều < 3ms, vượt xa target production (< 50ms p50). Data nhỏ (12 vectors) nên kết quả rất nhanh, nhưng cho thấy engine hoạt động đúng.

---

## 5. ĐÁNH GIÁ TÍNH NĂNG

| Tính năng | Trạng thái | Ghi chú |
|-----------|------------|---------|
| Vector search (Cosine similarity) | ✅ Hoạt động | Trả về kết quả sorted by score |
| Payload filter (keyword) | ✅ Hoạt động | Filter inline khi search |
| Multi-condition filter | ✅ Hoạt động | AND logic giữa nhiều điều kiện |
| Upsert (batch) | ✅ Hoạt động | 6 points/batch, idempotent |
| Update payload | ✅ Hoạt động | Đổi metadata không cần re-index vector |
| Delete points | ✅ Hoạt động | Xóa theo list ID |
| Scroll/Pagination | ✅ Hoạt động | next_page_offset cho phân trang |
| Snapshot backup | ✅ Hoạt động | File .snapshot có checksum |
| REST API | ✅ Hoạt động | PowerShell Invoke-RestMethod |
| Dashboard UI | ✅ Hoạt động | http://localhost:6333/dashboard |

---

## 6. LƯU Ý & HẠN CHẾ CỦA DEMO

| # | Hạn chế | Giải pháp khi lên Production |
|---|---------|-------------------------------|
| 1 | Vector giả lập (random) | Dùng BGE-M3 embedding model (1024d) |
| 2 | Chỉ dense search, chưa có sparse | BGE-M3 sinh cả dense + sparse → hybrid search |
| 3 | 12 vectors (quá nhỏ) | Production: 8-10M vectors |
| 4 | 1 node, không HA | Cluster 4 nodes, replica=2 |
| 5 | Không auth/TLS | API key + TLS bắt buộc |
| 6 | Không quantization | INT8 Scalar Quantization giảm RAM |
| 7 | Score thấp (do random vector) | Embedding thật sẽ cho score cao hơn nhiều |

---

## 7. KẾT LUẬN

### Demo thành công, xác nhận:

1. **Qdrant cài đặt dễ dàng** – 1 lệnh `docker compose up -d` là chạy.
2. **REST API đầy đủ** – CRUD, search, filter, snapshot đều hoạt động qua PowerShell.
3. **Payload filter hiệu quả** – Filter inline không ảnh hưởng latency (thậm chí nhanh hơn do giảm candidates).
4. **Tài nguyên nhẹ** – Máy 16GB chạy thoải mái, không ảnh hưởng hoạt động khác.
5. **Sẵn sàng cho bước tiếp theo** – Luồng đã rõ ràng, có thể scale lên cluster production.

### Bước tiếp theo:

- [ ] Triển khai embedding model BGE-M3 (test trên local với data thật)
- [ ] Test hybrid search (dense + sparse) với data tiếng Việt
- [ ] Benchmark latency với 10K-100K vectors
- [ ] Chuẩn bị hạ tầng VM cho cluster production
- [ ] Thiết lập auth + TLS + monitoring

---

*Báo cáo tạo tự động từ kết quả chạy demo ngày 29/07/2026.*
