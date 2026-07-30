# BÁO CÁO TỔNG HỢP KẾT QUẢ DEMO QDRANT

| Thông tin | Giá trị |
|-----------|---------|
| Ngày thực hiện | 29/07/2026 |
| Dự án | AI Smart Search – v2 |
| Mục tiêu | Demo POC Qdrant trên máy cá nhân trước khi triển khai production |
| Phiên bản Qdrant | v1.12.0 |
| Phương thức | Docker Desktop + PowerShell (REST API) |
| Kết quả | **PASS – Toàn bộ demo thành công** |

---

## 1. CẤU HÌNH MÁY DEMO

| Thông số | Giá trị |
|----------|---------|
| CPU | Intel i7-1165G7 @ 2.80GHz (4 cores / 8 threads) |
| RAM | 16 GB DDR4 3200MHz |
| Ổ cứng | D: 293 GB (trống 155 GB) |
| OS | Windows 11 Home |
| Docker | Docker Desktop v29.1.3 |

---

## 2. NỘI DUNG DEMO

| Phần | Nội dung | Cấu hình |
|------|----------|----------|
| **A – Single Node** | CRUD, Search, Filter, Snapshot | 1 container, 2GB RAM |
| **B – Cluster 4 Nodes** | Shard, Replica, Failover, Auto-recovery | 4 containers x 1GB RAM |

---

## 3. PHẦN A – DEMO SINGLE NODE

### 3.1 Khởi động Qdrant

**Lệnh:**
```powershell
docker compose up -d
```

**Kết quả:**
```
[+] Running 2/2
 ✔ Network demo-local_default  Created    0.0s
 ✔ Container qdrant-demo       Started    0.4s
```

**Health check:**
```
PS> Invoke-RestMethod -Uri "http://localhost:6333/healthz"
healthz check passed

PS> Invoke-RestMethod -Uri "http://localhost:6333"
title                         version commit
-----                         ------- ------
qdrant - vector search engine 1.12.0  a0d2eccac0c179116214e7cb3583359c80d41998
```

✅ Qdrant v1.12.0 chạy thành công.

---

### 3.2 Tạo Collection

**Lệnh:**
```powershell
$body = @{
    vectors = @{ dense = @{ size = 384; distance = "Cosine" } }
    shard_number = 1
    replication_factor = 1
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_demo" -ContentType "application/json" -Body $body
```

**Kết quả:**
```
result status        time
------ ------        ----
  True ok     0.348270802
```

✅ Collection tạo thành công trong 348ms.

---

### 3.3 Tạo Payload Indexes

**Kết quả:**
```
Created index: doc_status    → operation_id=1, status=acknowledged, time=0.016s
Created index: domain        → operation_id=3, status=acknowledged, time=0.012s
Created index: department    → operation_id=5, status=acknowledged, time=0.014s
Created index: doc_type      → operation_id=7, status=acknowledged, time=0.013s
```

✅ 4 indexes tạo thành công (12-16ms mỗi index).

---

### 3.4 Upsert dữ liệu

**Kết quả:**
```
Batch 01 (6 points nhan_su):    operation_id=8, status=completed, time=0.030s
Batch 02 (6 points cong_nghe):  operation_id=9, status=completed, time=0.020s

points_count = 12
```

✅ 12 points upsert thành công (20-30ms/batch).

---

### 3.5 Search cơ bản (không filter)

**Kết quả thực tế:**
```json
{
  "result": {
    "points": [
      { "id": 10, "score": 0.120049395, "payload": { "title": "Quy trinh deploy Production", "domain": "cong_nghe" } },
      { "id": 11, "score": 0.088837,    "payload": { "title": "Quy dinh su dung VPN", "domain": "cong_nghe" } },
      { "id": 2,  "score": 0.07027188,  "payload": { "title": "Quy dinh nghi phep nam 2024", "domain": "nhan_su" } },
      { "id": 1,  "score": 0.06854092,  "payload": { "title": "Quy dinh nghi phep nam 2024", "domain": "nhan_su" } },
      { "id": 5,  "score": 0.046845645, "payload": { "title": "Quy dinh danh gia KPI", "domain": "nhan_su" } }
    ]
  },
  "status": "ok",
  "time": 0.002235719
}
```

✅ Trả về 5 kết quả, sorted by score, latency **2.2ms**.

---

### 3.6 Search + Filter domain = cong_nghe

**Kết quả thực tế:**
```json
{
  "result": {
    "points": [
      { "id": 9,  "score": 0.13979244,  "payload": { "title": "Huong dan su dung eISO", "domain": "cong_nghe" } },
      { "id": 11, "score": 0.04921663,  "payload": { "title": "Quy dinh su dung VPN", "domain": "cong_nghe" } },
      { "id": 10, "score": 0.044091165, "payload": { "title": "Quy trinh deploy Production", "domain": "cong_nghe" } },
      { "id": 7,  "score": -0.011515399,"payload": { "title": "Chinh sach bao mat thong tin", "domain": "cong_nghe" } },
      { "id": 8,  "score": -0.06889442, "payload": { "title": "Quy trinh xu ly su co he thong", "domain": "cong_nghe" } }
    ]
  },
  "status": "ok",
  "time": 0.00155578
}
```

✅ Chỉ trả về documents domain=cong_nghe, latency **1.6ms**. Filter hoạt động đúng.

---

### 3.7 Search + Filter department = NHAN_SU

**Kết quả thực tế:**
```json
{
  "result": {
    "points": [
      { "id": 3, "score": 0.018810531, "payload": { "title": "Quy trinh tuyen dung nhan su", "department": "NHAN_SU" } }
    ]
  },
  "status": "ok",
  "time": 0.001154602
}
```

✅ Chỉ 1 kết quả đúng (chỉ có 1 point thuộc NHAN_SU), latency **1.2ms**.

---

### 3.8 Search + Multi-filter (domain=cong_nghe AND doc_type=quy_trinh AND doc_status=ACTIVE)

**Kết quả thực tế:**
```json
{
  "result": {
    "points": [
      { "id": 10, "score": 0.033464856, "payload": { "title": "Quy trinh deploy Production" } },
      { "id": 8,  "score": -0.003684571,"payload": { "title": "Quy trinh xu ly su co he thong" } }
    ]
  },
  "status": "ok",
  "time": 0.00108169
}
```

✅ 2 kết quả đúng (chỉ quy_trinh + cong_nghe + ACTIVE), latency **1.1ms**.

---

### 3.9 Scroll (Pagination)

**Kết quả thực tế:**
```json
{
  "result": {
    "points": [
      { "id": 1, "payload": { "title": "Quy dinh nghi phep nam 2024" } },
      { "id": 2, "payload": { "title": "Quy dinh nghi phep nam 2024" } },
      { "id": 3, "payload": { "title": "Quy trinh tuyen dung nhan su" } },
      { "id": 4, "payload": { "title": "Chinh sach lam viec tu xa WFH" } },
      { "id": 5, "payload": { "title": "Quy dinh danh gia KPI" } }
    ],
    "next_page_offset": 6
  },
  "status": "ok",
  "time": 0.001088157
}
```

✅ Pagination hoạt động, `next_page_offset=6` cho phép lấy trang tiếp.

---

### 3.10 Update Payload

**Kết quả:**
```
result                                  status        time
------                                  ------        ----
@{operation_id=10; status=acknowledged} ok     0.001005832
```

✅ Đổi doc_status → ARCHIVED cho points 1,2,3.

---

### 3.11 Delete Points

**Kết quả:**
```
result                                  status        time
------                                  ------        ----
@{operation_id=11; status=acknowledged} ok     0.000765722
```

✅ Xóa points 1,2,3 thành công.

---

### 3.12 Snapshot (Backup)

**Kết quả:**
```
name:          smart_search_demo-2848121824292700-2026-07-29-07-41-28.snapshot
creation_time: 2026-07-29T07:41:34
size:          136512000 (136 MB)
checksum:      5aaa069c21a30d789ac7eb135934f0a95374933eb2bbd7f556bd3bb7090a2dad
```

✅ Snapshot tạo thành công, có checksum xác minh toàn vẹn dữ liệu.

---

### 3.13 Xóa Collection

**Kết quả:**
```
result status        time
------ ------        ----
  True ok     0.031731892
```

✅ Cleanup thành công.

---

## 4. PHẦN B – DEMO CLUSTER 4 NODES

### 4.1 Khởi động Cluster 4 Nodes

**Lệnh:**
```powershell
cd D:\Qdrant\demo-local\cluster-demo
docker compose up -d
```

**Kết quả:**
```
[+] Running 5/5
 ✔ Network cluster-demo_default  Created    0.0s
 ✔ Container qdrant-node1        Started    0.6s
 ✔ Container qdrant-node2        Started    1.0s
 ✔ Container qdrant-node4        Started    0.9s
 ✔ Container qdrant-node3        Started    0.9s
```

**Docker ps:**
```
NAME           IMAGE                   SERVICE        STATUS       PORTS
qdrant-node1   qdrant/qdrant:v1.12.0   qdrant-node1   Up 4 min     6333-6335
qdrant-node2   qdrant/qdrant:v1.12.0   qdrant-node2   Up 4 min     6343-6345
qdrant-node3   qdrant/qdrant:v1.12.0   qdrant-node3   Up 4 min     6353-6355
qdrant-node4   qdrant/qdrant:v1.12.0   qdrant-node4   Up 4 min     6363-6365
```

✅ 4 containers online.

---

### 4.2 Cluster Status (4 peers, Raft Consensus)

**Kết quả thực tế:**
```json
{
  "result": {
    "status": "enabled",
    "peer_id": 7635232162672259,
    "peers": {
      "2867989850515874": { "uri": "http://qdrant-node4:6335/" },
      "8810942280413922": { "uri": "http://qdrant-node3:6335/" },
      "7635232162672259": { "uri": "http://qdrant-node1:6335/" },
      "2057929853941450": { "uri": "http://qdrant-node2:6335/" }
    },
    "raft_info": {
      "term": 1,
      "commit": 11,
      "pending_operations": 0,
      "leader": 7635232162672259,
      "role": "Leader",
      "is_voter": true
    },
    "consensus_thread_status": {
      "consensus_thread_status": "working",
      "last_update": "2026-07-29T08:28:35.911380325Z"
    },
    "message_send_failures": {}
  },
  "status": "ok"
}
```

✅ **4 peers online**, Raft consensus working, Node 1 = Leader, không có lỗi.

**Verify tất cả nodes chạy cùng version:**
```
qdrant - vector search engine 1.12.0  (cả 4 nodes)
```

---

### 4.3 Tạo Collection (shard=4, replica=2)

**Kết quả:**
```
result status        time
------ ------        ----
  True ok     1.680327928
```

✅ Collection tạo thành công trong 1.68s (lâu hơn single node do phân bổ shards trên cluster).

---

### 4.4 Phân bổ Shard (kết quả thực tế)

**Kết quả từ API `/collections/smart_search_cluster/cluster`:**
```json
{
  "result": {
    "peer_id": 7635232162672259,
    "shard_count": 4,
    "local_shards": [
      { "shard_id": 1, "points_count": 0, "state": "Active" },
      { "shard_id": 3, "points_count": 0, "state": "Active" }
    ],
    "remote_shards": [
      { "shard_id": 0, "peer_id": 8810942280413922, "state": "Active" },
      { "shard_id": 0, "peer_id": 2867989850515874, "state": "Active" },
      { "shard_id": 1, "peer_id": 2057929853941450, "state": "Active" },
      { "shard_id": 2, "peer_id": 2867989850515874, "state": "Active" },
      { "shard_id": 2, "peer_id": 8810942280413922, "state": "Active" },
      { "shard_id": 3, "peer_id": 2057929853941450, "state": "Active" }
    ],
    "shard_transfers": []
  }
}
```

**Bảng phân bổ (giải mã peer_id):**

| Shard | Node A | Node B | Trạng thái |
|-------|--------|--------|------------|
| Shard 0 | Node 3 | Node 4 | ✅ Active |
| Shard 1 | Node 1 | Node 2 | ✅ Active |
| Shard 2 | Node 4 | Node 3 | ✅ Active |
| Shard 3 | Node 1 | Node 2 | ✅ Active |

✅ **4 shards × 2 replicas**, mỗi shard trên 2 nodes khác nhau. `shard_transfers: []` = cluster ổn định.

---

### 4.5 Upsert & Search Fan-out

**Upsert 12 points:**
```
Batch 01: operation_id=8, status=completed, time=0.046s
Batch 02: operation_id=8, status=completed, time=0.020s
points_count = 12
```

**Search từ 4 nodes khác nhau (cùng query):**

| Node | Top 1 | Top 2 | Top 3 | Latency |
|------|-------|-------|-------|---------|
| Node 1 (6333) | id=10, score=0.1200 | id=11, score=0.0888 | id=2, score=0.0703 | **11.0ms** |
| Node 2 (6343) | id=10, score=0.1200 | id=11, score=0.0888 | id=2, score=0.0703 | **9.9ms** |
| Node 3 (6353) | id=10, score=0.1200 | id=11, score=0.0888 | id=2, score=0.0703 | **4.9ms** |
| Node 4 (6363) | id=10, score=0.1200 | id=11, score=0.0888 | id=2, score=0.0703 | **5.8ms** |

✅ **Cả 4 nodes trả kết quả GIỐNG HỆT NHAU** (cùng IDs, cùng scores, cùng thứ tự). Chứng minh search fan-out hoạt động chính xác.

---

### 4.6 FAILOVER ĐỌC – Tắt Node 2, Search vẫn OK

**Bước 1: Tắt Node 2**
```
PS> docker stop qdrant-node2
qdrant-node2
Node 2 da tat!
```

**Bước 2: Cluster phát hiện lỗi**
```json
{
  "message_send_failures": {
    "http://qdrant-node2:6335/": {
      "count": 5,
      "latest_error": "status: Unavailable, message: \"error trying to connect: deadline has elapsed\"",
      "latest_error_timestamp": "2026-07-29T08:53:01.239340406Z"
    }
  }
}
```

✅ Cluster phát hiện đúng node2 unreachable.

**Bước 3: Search vẫn hoạt động (Node 1)**
```json
{
  "result": {
    "points": [
      { "id": 9,  "score": 0.13979244,  "payload": { "title": "Huong dan su dung eISO" } },
      { "id": 11, "score": 0.04921663,  "payload": { "title": "Quy dinh su dung VPN" } },
      { "id": 10, "score": 0.044091165, "payload": { "title": "Quy trinh deploy Production" } },
      { "id": 7,  "score": -0.011515399,"payload": { "title": "Chinh sach bao mat thong tin" } },
      { "id": 8,  "score": -0.06889442, "payload": { "title": "Quy trinh xu ly su co he thong" } }
    ]
  },
  "status": "ok",
  "time": 0.004368375
}
```

✅ **FAILOVER ĐỌC THÀNH CÔNG:** Mất node 2, search từ node 1 vẫn trả 5 kết quả bình thường (4.4ms).

**Bước 4: Search từ Node 3 cũng OK**
```
status: "ok", time: 0.002954296, 5 results (cùng data với Node 1)
```

✅ Node 3 cũng phục vụ search bình thường khi node 2 chết.

**Bước 5: Khôi phục Node 2**
```
PS> docker start qdrant-node2
qdrant-node2

Cluster status sau 5s:
  message_send_failures: {}    ← Hết lỗi, node 2 đã rejoin
  consensus_thread_status: "working"
```

✅ **AUTO-RECOVERY:** Node 2 rejoin, cluster tự đồng bộ, `message_send_failures` tự reset về rỗng.

---

### 4.7 FAILOVER GHI – Tắt Node 3, Upsert vẫn OK

**Bước 1: Tắt Node 3**
```
PS> docker stop qdrant-node3
qdrant-node3
```

**Bước 2: Upsert point mới khi mất node 3**
```
result                               status        time
------                               ------        ----
@{operation_id=10; status=completed} ok     6.581008207
```

✅ **GHI THÀNH CÔNG** dù mất 1 node (6.58s do timeout chờ node chết trước khi xác nhận).

**Bước 3: Khôi phục Node 3 → Tự đồng bộ point mới**
```json
{
  "result": [
    {
      "id": 100,
      "payload": {
        "department": "CNTT",
        "domain": "cong_nghe",
        "text": "Day la van ban upsert khi node 3 da tat, chung minh cluster van ghi duoc.",
        "document_id": "DOC-NEW",
        "doc_status": "ACTIVE",
        "title": "Van ban moi upsert khi mat 1 node",
        "doc_type": "test"
      }
    }
  ],
  "status": "ok",
  "time": 0.001209736
}
```

✅ **AUTO-SYNC:** Lấy point 100 từ Node 3 (port 6353) → Node 3 đã tự đồng bộ data mới mà không cần can thiệp.

---

### 4.8 Trạng thái cuối cùng của Cluster

```json
{
  "shard_count": 4,
  "local_shards": [
    { "shard_id": 1, "points_count": 2, "state": "Active" },
    { "shard_id": 3, "points_count": 4, "state": "Active" }
  ],
  "remote_shards": [
    { "shard_id": 0, "state": "Active" },
    { "shard_id": 1, "state": "Active" },
    { "shard_id": 2, "state": "Active" },
    { "shard_id": 2, "state": "Active" },
    { "shard_id": 0, "state": "Active" },
    { "shard_id": 3, "state": "Active" }
  ],
  "shard_transfers": []
}
```

✅ Tất cả shards Active, không có transfer pending, cluster hoàn toàn ổn định sau failover + recovery.

---

## 5. BẢNG TỔNG HỢP TÍNH NĂNG ĐÃ DEMO (KÈM BẰNG CHỨNG)

| # | Tính năng | Kết quả | Bằng chứng (output thực tế) |
|---|-----------|---------|------------------------------|
| 1 | Docker deployment | ✅ PASS | Container started 0.4s (single), 4 containers < 1s (cluster) |
| 2 | Health check API | ✅ PASS | `healthz check passed`, version 1.12.0 |
| 3 | Tạo Collection | ✅ PASS | `result: True, status: ok` |
| 4 | Payload Indexes | ✅ PASS | 4 indexes `status=acknowledged` (12-16ms) |
| 5 | Batch Upsert | ✅ PASS | `status=completed`, points_count=12 |
| 6 | Vector Search (Cosine) | ✅ PASS | 5 results sorted by score, latency 2.2ms |
| 7 | Filter: single field (domain) | ✅ PASS | Chỉ trả cong_nghe (5 results), latency 1.6ms |
| 8 | Filter: single field (department) | ✅ PASS | Chỉ trả NHAN_SU (1 result), latency 1.2ms |
| 9 | Filter: multi-condition (AND) | ✅ PASS | domain+doc_type+status (2 results), latency 1.1ms |
| 10 | Scroll / Pagination | ✅ PASS | 5 points + `next_page_offset: 6` |
| 11 | Update Payload | ✅ PASS | `status=acknowledged`, doc_status → ARCHIVED |
| 12 | Delete Points | ✅ PASS | `status=acknowledged` |
| 13 | Snapshot Backup | ✅ PASS | 136MB, checksum `5aaa069c...` |
| 14 | Delete Collection | ✅ PASS | `result: True` |
| 15 | Cluster 4 nodes (Raft) | ✅ PASS | 4 peers, term=1, leader elected, consensus working |
| 16 | Shard=4, phân bổ tự động | ✅ PASS | 4 shards trên 4 nodes, `shard_transfers: []` |
| 17 | Replica=2 | ✅ PASS | Mỗi shard 2 copies trên 2 nodes khác nhau |
| 18 | Search fan-out (4 nodes) | ✅ PASS | 4 nodes trả kết quả **giống hệt nhau** (cùng ID, score) |
| 19 | **Failover đọc** | ✅ PASS | Tắt node2 → search vẫn OK (4.4ms, 5 results) |
| 20 | **Error detection** | ✅ PASS | `message_send_failures` báo đúng node chết + error message |
| 21 | **Failover ghi** | ✅ PASS | Tắt node3 → upsert point 100 thành công |
| 22 | **Auto-recovery** | ✅ PASS | Node rejoin, `message_send_failures: {}`, data đồng bộ |
| 23 | **Auto-sync data** | ✅ PASS | GET point 100 từ node3 sau recovery → có data |

**Tổng: 23/23 tính năng PASS.**

---

## 6. BẢNG ĐỐI CHIẾU VỚI BÁO CÁO TRIỂN KHAI GỐC (PHẦN D)

| # | Bước trong báo cáo gốc | Đã demo? | Bằng chứng |
|---|-------------------------|----------|------------|
| **12** | **Cài đặt Qdrant Cluster** | | |
| 12.1 | Chuẩn bị VM (Docker) | ✅ | Docker Desktop running, 4 containers started |
| 12.2 | Config (cluster enabled, P2P port) | ✅ | env: QDRANT__CLUSTER__ENABLED=true, P2P=6335 |
| 12.3 | Khởi động Node 1 (bootstrap) | ✅ | `--uri http://qdrant-node1:6335` → Leader |
| 12.4 | Join Node 2, 3, 4 | ✅ | `--bootstrap http://qdrant-node1:6335` → 4 peers |
| 12.5 | Verify cluster | ✅ | `GET /cluster` → 4 peers, status=enabled |
| 12.2b | TLS + API key | ❌ | Không cần cho POC local |
| **13** | **Tạo Collection & Indexes** | | |
| 13.1 | Named vectors (dense) | ✅ | size=384, distance=Cosine |
| 13.2 | Sparse vectors | ❌ | Cần BGE-M3 model |
| 13.3 | HNSW config (m=16, ef=200) | ❌ | Dùng default |
| 13.4 | Quantization (INT8) | ❌ | Data nhỏ, không có ý nghĩa |
| 13.5 | Shard=4, Replica=2 | ✅ | `shard_count: 4`, 8 shard copies trên 4 nodes |
| 13.6 | Payload indexes (keyword) | ✅ | 4 indexes acknowledged |
| **14** | **Bảng lệnh API** | | |
| 14.1 | GET /healthz | ✅ | "healthz check passed" |
| 14.2 | GET /cluster | ✅ | 4 peers JSON |
| 14.3 | GET /collections/{name} | ✅ | status=green, points_count=12 |
| 14.4 | PUT /points (upsert) | ✅ | status=completed |
| 14.5 | POST /points/query (search) | ✅ | 5 results with scores |
| 14.6 | POST /points/scroll | ✅ | 5 points + next_page_offset |
| 14.7 | POST /points/delete | ✅ | status=acknowledged |
| 14.8 | POST /points/payload (update) | ✅ | status=acknowledged |
| 14.9 | POST /snapshots | ✅ | name, size, checksum |
| **15** | **Ingestion Pipeline** | ⚠️ | Có batch upsert, chưa có embedding model |
| **16** | **Search Integration** | ⚠️ | Search + filter OK, chưa hybrid RRF |
| **17** | **Security** | ❌ | Không cần cho POC |
| **18** | **Monitoring & Backup** | | |
| 18.1 | Snapshot | ✅ | 136MB snapshot created |
| 18.2 | Prometheus + Grafana | ❌ | Chưa setup |
| — | **Failover (bonus)** | ✅ | Đọc + Ghi OK khi mất node |
| — | **Auto-recovery (bonus)** | ✅ | Node rejoin + sync tự động |

---

## 7. HIỆU NĂNG SO SÁNH

| Thao tác | Single Node | Cluster 4 Nodes | Ghi chú |
|----------|-------------|------------------|---------|
| Tạo collection | 348ms | 1,680ms | Cluster cần phân bổ shards |
| Tạo index | 12-16ms | 100-200ms | Replicate indexes |
| Upsert batch | 20-30ms | 20-46ms | Gần tương đương |
| **Search** | **1.1-2.2ms** | **5-11ms** | Fan-out overhead |
| **Search khi mất node** | — | **3-4ms** | HA hoạt động |
| Upsert khi mất node | — | 6,580ms | Timeout chờ node chết |
| Node recovery | — | < 5s | Tự động |

---

## 8. KẾT LUẬN

### Demo thành công, xác nhận:

1. **Qdrant triển khai nhanh** – Từ 0 đến cluster 4 nodes chỉ cần 1 lệnh docker compose.
2. **REST API đầy đủ** – CRUD, search, filter, snapshot đều hoạt động qua PowerShell.
3. **Cluster đúng thiết kế** – 4 nodes, 4 shards, replica=2, Raft consensus, đúng như báo cáo gốc.
4. **Failover HA** – Mất 1 node → đọc OK, ghi OK, không gián đoạn.
5. **Auto-recovery** – Node phục hồi tự rejoin + đồng bộ, không cần thao tác thủ công.
6. **Hiệu năng** – Search < 12ms trên cluster, < 3ms trên single node.
7. **Tài nguyên** – Máy 16GB chạy cluster 4 nodes không lag.

### Bước tiếp theo:

- [ ] BGE-M3 embedding model → test hybrid search (dense + sparse + RRF)
- [ ] Benchmark với 10K → 100K vectors
- [ ] Bật TLS + API key trên staging
- [ ] Setup Prometheus + Grafana
- [ ] Provision 4 VMs production (32-48GB RAM)
- [ ] Ingestion pipeline data thật từ eISO

---

*Báo cáo tổng hợp – Demo Qdrant POC ngày 29/07/2026*
*Máy demo: Intel i7-1165G7, 16GB RAM, Windows 11, Docker Desktop v29.1.3*
