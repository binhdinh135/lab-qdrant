# BÁO CÁO KẾT QUẢ DEMO QDRANT CLUSTER (4 NODES, SHARD & REPLICA)

| Thông tin | Giá trị |
|-----------|---------|
| Ngày thực hiện | 29/07/2026 |
| Mục tiêu | Demo cluster Qdrant 4 nodes: shard, replica, failover, auto-recovery |
| Phiên bản Qdrant | v1.12.0 |
| Phương thức | Docker Compose (4 containers) + PowerShell REST API |
| Kết quả tổng quan | **PASS – Toàn bộ chạy thành công, failover hoạt động đúng** |

---

## 1. CẤU HÌNH CLUSTER

| Thông số | Giá trị |
|----------|---------|
| Số nodes | 4 (giả lập 4 VMs bằng 4 Docker containers) |
| RAM/node | Giới hạn 1 GB |
| Ports | Node1: 6333, Node2: 6343, Node3: 6353, Node4: 6363 |
| P2P Protocol | Raft consensus (port 6335 nội bộ) |
| Leader | Node 1 (peer_id: 7635232162672259) |

### Cấu hình Collection

| Thông số | Giá trị |
|----------|---------|
| Collection name | smart_search_cluster |
| Vector size | 384 dimensions (Cosine) |
| **Shard number** | **4** |
| **Replication factor** | **2** |
| Write consistency | 1 (ghi thành công nếu 1 replica xác nhận) |
| Payload indexes | 4 (doc_status, domain, department, doc_type) |

---

## 2. KẾT QUẢ TỪNG BƯỚC

### 2.1 Khởi động Cluster

| Bước | Kết quả |
|------|---------|
| `docker compose up -d` | ✅ 4 containers started (< 1s) |
| Cluster status | ✅ 4 peers online, Raft consensus working |
| Leader election | ✅ Node 1 là Leader (term=1) |
| Tất cả nodes version | ✅ Qdrant v1.12.0 |

**Cluster info:**
```
peers: 4 nodes (node1, node2, node3, node4)
raft_info: term=1, commit=11, role=Leader
consensus_thread_status: working
message_send_failures: (trống - không lỗi)
```

### 2.2 Tạo Collection (shard + replica)

| Thao tác | Kết quả | Thời gian |
|----------|---------|-----------|
| Tạo collection (4 shards, R=2) | ✅ status: ok | 1.68s |

**Nhận xét:** Thời gian tạo collection lâu hơn single node (1.68s vs 0.35s) do phải phân bổ shards + replicas trên 4 nodes → đây là hành vi đúng.

### 2.3 Phân bổ Shard (kết quả thực tế)

Từ góc nhìn Node 1 (Leader):

| Shard | Copy A (Primary) | Copy B (Replica) | Trạng thái |
|-------|-------------------|-------------------|------------|
| Shard 0 | Node 3 | Node 4 | ✅ Active |
| Shard 1 | **Node 1** | Node 2 | ✅ Active |
| Shard 2 | Node 4 | Node 3 | ✅ Active |
| Shard 3 | **Node 1** | Node 2 | ✅ Active |

**Nhận xét:**
- Mỗi shard có đúng 2 copies trên 2 nodes khác nhau ✅
- Mất bất kỳ 1 node → mỗi shard vẫn còn ít nhất 1 copy active ✅
- `shard_transfers: []` → không có transfer đang chạy, cluster ổn định ✅

### 2.4 Upsert dữ liệu

| Batch | Kết quả | Thời gian |
|-------|---------|-----------|
| Batch 01 (6 points) | ✅ completed | 46ms |
| Batch 02 (6 points) | ✅ completed | 20ms |
| **Tổng points** | **12** | |

### 2.5 Search Fan-out (từ 4 nodes khác nhau)

**Kết quả: cả 4 nodes trả về KẾT QUẢ GIỐNG HỆT NHAU.**

| Node | Top 1 (ID, Score) | Top 2 (ID, Score) | Top 3 (ID, Score) | Latency |
|------|--------------------|--------------------|--------------------|---------| 
| Node 1 (6333) | id=10, 0.1200 | id=11, 0.0888 | id=2, 0.0703 | 11.0ms |
| Node 2 (6343) | id=10, 0.1200 | id=11, 0.0888 | id=2, 0.0703 | 9.9ms |
| Node 3 (6353) | id=10, 0.1200 | id=11, 0.0888 | id=2, 0.0703 | 4.9ms |
| Node 4 (6363) | id=10, 0.1200 | id=11, 0.0888 | id=2, 0.0703 | 5.8ms |

**Nhận xét:**
- ✅ Kết quả NHẤT QUÁN giữa tất cả nodes (cùng IDs, cùng scores, cùng thứ tự)
- ✅ Chứng minh search fan-out hoạt động: query gửi đến bất kỳ node nào đều merge kết quả từ tất cả shards
- ✅ Latency cluster (5-11ms) cao hơn single node (2ms) do overhead fan-out → đây là trade-off bình thường

---

## 3. DEMO FAILOVER (ĐỌC) – TẮT NODE 2

### 3.1 Tắt Node 2

```
docker stop qdrant-node2 → OK
```

### 3.2 Cluster Status sau khi mất Node 2

| Thông tin | Giá trị |
|-----------|---------|
| Cluster status | ✅ enabled (vẫn hoạt động) |
| Peers | 4 (node2 vẫn trong danh sách nhưng unreachable) |
| Leader | Node 1 (không đổi) |
| Raft commit | 24 (tiếp tục hoạt động) |
| message_send_failures | ❌ node2: "Unavailable - error trying to connect: deadline has elapsed" |

### 3.3 Search khi mất Node 2

| Node | Kết quả | Latency |
|------|---------|---------|
| Node 1 (6333) | ✅ 5 results, đúng data | 4.4ms |
| Node 3 (6353) | ✅ 5 results, đúng data | 3.0ms |

**Kết quả search từ Node 1 khi Node 2 đã chết:**

| # | Score | Doc ID | Title |
|---|-------|--------|-------|
| 1 | 0.1398 | DOC-008 | Huong dan su dung eISO |
| 2 | 0.0492 | DOC-010 | Quy dinh su dung VPN |
| 3 | 0.0441 | DOC-009 | Quy trinh deploy Production |
| 4 | -0.0115 | DOC-006 | Chinh sach bao mat thong tin |
| 5 | -0.0689 | DOC-007 | Quy trinh xu ly su co he thong |

**→ FAILOVER ĐỌC THÀNH CÔNG: Mất 1 node, search vẫn trả kết quả bình thường nhờ replica.**

### 3.4 Khôi phục Node 2

| Thao tác | Kết quả |
|----------|---------|
| `docker start qdrant-node2` | ✅ Started |
| Cluster status sau 5s | ✅ 4 peers active, `message_send_failures: {}` (hết lỗi) |

**→ AUTO-RECOVERY: Node 2 tự rejoin cluster, tự đồng bộ, không cần thao tác thủ công.**

---

## 4. DEMO FAILOVER (GHI) – TẮT NODE 3, UPSERT VẪN OK

### 4.1 Tắt Node 3

```
docker stop qdrant-node3 → OK
```

### 4.2 Upsert khi mất Node 3

| Thao tác | Kết quả | Thời gian |
|----------|---------|-----------|
| Upsert point id=100 | ✅ completed | 6.58s |

**Nhận xét:** Ghi thành công dù mất 1 node. Thời gian lâu hơn bình thường (6.58s vs ~46ms) do Qdrant cố gắng liên lạc node3 trước khi timeout → đây là hành vi đúng khi `write_consistency_factor=1`.

### 4.3 Khôi phục Node 3 → Tự đồng bộ point mới

| Thao tác | Kết quả |
|----------|---------|
| `docker start qdrant-node3` | ✅ Started |
| GET point 100 từ Node 3 | ✅ Tìm thấy! Data đã đồng bộ |

**Verify từ Node 3 (port 6353):**
```json
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
```

**→ FAILOVER GHI + AUTO-SYNC THÀNH CÔNG:**
- Ghi vào cluster khi mất 1 node: ✅
- Node phục hồi tự đồng bộ data mới: ✅

---

## 5. TRẠNG THÁI CUỐI CÙNG CỦA CLUSTER

Sau tất cả thao tác failover + recovery:

| Shard | Points | Trạng thái | Nodes |
|-------|--------|------------|-------|
| Shard 0 | — | ✅ Active | Node 3, Node 4 |
| Shard 1 | 2 | ✅ Active | Node 1, Node 2 |
| Shard 2 | — | ✅ Active | Node 4, Node 3 |
| Shard 3 | 4 | ✅ Active | Node 1, Node 2 |

- `shard_transfers: []` → không có transfer pending, cluster hoàn toàn ổn định
- Tổng: 13 points (12 ban đầu + 1 upsert khi failover)

---

## 6. TỔNG HỢP HIỆU NĂNG CLUSTER

| Thao tác | Latency | So sánh Single Node | Ghi chú |
|----------|---------|---------------------|---------|
| Tạo collection | 1.68s | 0.35s (single) | Phân bổ shards + replicas |
| Tạo indexes | 100-200ms | 12-16ms (single) | Replicate indexes |
| Upsert (batch 6) | 20-46ms | 20-30ms (single) | Gần tương đương |
| Search (cluster healthy) | 5-11ms | 2ms (single) | Fan-out overhead |
| Search (mất 1 node) | 3-4ms | — | Nhanh hơn do ít node fan-out |
| Upsert (mất 1 node) | 6.58s | — | Timeout chờ node chết |
| Recovery (node rejoin) | < 5s | — | Tự động |

---

## 7. ĐÁNH GIÁ TÍNH NĂNG CLUSTER

| Tính năng | Trạng thái | Bằng chứng |
|-----------|------------|------------|
| Cluster formation (4 nodes) | ✅ PASS | 4 peers online, Raft consensus |
| Shard distribution (4 shards) | ✅ PASS | Shards phân bổ đều trên 4 nodes |
| Replication (factor=2) | ✅ PASS | Mỗi shard có 2 copies trên 2 nodes khác nhau |
| Search fan-out | ✅ PASS | 4 nodes trả kết quả giống hệt nhau |
| **Failover đọc** | ✅ PASS | Tắt node2 → search vẫn OK |
| **Failover ghi** | ✅ PASS | Tắt node3 → upsert vẫn thành công |
| **Auto-recovery** | ✅ PASS | Node rejoin + tự đồng bộ data mới |
| Raft consensus | ✅ PASS | Leader election, commit tiếp tục khi mất node |
| Error detection | ✅ PASS | `message_send_failures` báo đúng node chết |
| Error clearing | ✅ PASS | Sau recovery, failures tự reset về rỗng |

---

## 8. KẾT LUẬN

### Demo cluster thành công, xác nhận:

1. **Cluster 4 nodes hoạt động đúng** – Raft consensus, leader election, peer discovery tự động.
2. **Shard phân tán** – 4 shards chia đều data, search fan-out merge kết quả từ tất cả shards.
3. **Replica đảm bảo HA** – Mất 1 node, cluster vẫn phục vụ đọc VÀ ghi bình thường.
4. **Auto-recovery** – Node phục hồi tự rejoin + đồng bộ data mới không cần can thiệp.
5. **Nhất quán dữ liệu** – Search từ bất kỳ node nào đều cho kết quả giống nhau.
6. **Tài nguyên hợp lý** – 4 nodes × 1GB RAM chạy thoải mái trên máy 16GB.

### So sánh Demo vs Production

| Tiêu chí | Demo (local) | Production |
|----------|-------------|------------|
| Nodes | 4 containers / 1 máy | 4 VMs riêng biệt |
| RAM/node | 1 GB | 32-48 GB |
| Shards | 4 | 4-8 |
| Replica | 2 | 2 |
| Data | 13 vectors | 8-10M vectors |
| Network | Docker bridge | Private network + firewall |
| Auth | Không | API key + TLS |
| Monitoring | Không | Prometheus + Grafana |

### Những điểm production cần thêm:

- [ ] TLS + API key authentication
- [ ] Monitoring (Prometheus /metrics → Grafana)
- [ ] Alerting (latency p95 > 200ms, RAM > 85%)
- [ ] Scheduled snapshots (daily backup)
- [ ] Load Balancer trước cluster
- [ ] Network firewall rules
- [ ] Quantization (INT8) cho data lớn

---

*Báo cáo tạo từ kết quả demo cluster ngày 29/07/2026.*
