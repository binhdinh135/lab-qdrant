# KỊCH BẢN DEMO QDRANT CLUSTER (4 NODES, SHARD, REPLICA)

> Demo cluster Qdrant trên 1 máy Windows bằng cách chạy 4 containers (giả lập 4 VMs).
> Giới hạn mỗi node 1GB RAM → tổng 4GB → máy 16GB vẫn thoải mái.
> Đúng kiến trúc production: 4 nodes, 4 shards, replica=2.

## Sơ đồ cluster demo

```
┌─────────────────────────────────────────────────────────────────┐
│                  MÁY CÁ NHÂN (16GB RAM)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │   NODE 1    │ │   NODE 2    │ │   NODE 3    │ │   NODE 4   ││
│  │ port: 6333  │ │ port: 6343  │ │ port: 6353  │ │ port: 6363 ││
│  │ RAM: 1GB    │ │ RAM: 1GB    │ │ RAM: 1GB    │ │ RAM: 1GB   ││
│  │ (bootstrap) │ │ (join)      │ │ (join)      │ │ (join)     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘│
│        ↕                ↕                ↕              ↕        │
│        └──────────── P2P (port 6335) ───────────────────┘        │
│                                                                  │
│  Collection: smart_search_cluster                                │
│  Shards: 4 (mỗi node hold 1 shard primary)                      │
│  Replica: 2 (mỗi shard có 2 copies trên 2 nodes khác nhau)      │
└─────────────────────────────────────────────────────────────────┘
```

## Tài nguyên sử dụng

| Thành phần | RAM |
|------------|-----|
| Docker Desktop | ~1.5 GB |
| Node 1 | max 1 GB |
| Node 2 | max 1 GB |
| Node 3 | max 1 GB |
| Node 4 | max 1 GB |
| **Tổng** | **~5.5 GB** |

→ Máy 16GB còn ~10GB cho Windows. **Không lag.**

---

## BƯỚC 1: Start cluster 4 nodes

```powershell
cd D:\Qdrant\demo-local\cluster-demo
docker compose up -d
```

Đợi ~10 giây để các node join cluster.

Kiểm tra:
```powershell
docker compose ps
```

---

## BƯỚC 2: Kiểm tra cluster status

```powershell
Invoke-RestMethod -Uri "http://localhost:6333/cluster" | ConvertTo-Json -Depth 5
```

→ Kỳ vọng: thấy 4 peers (4 nodes đã join).

Kiểm tra từng node:
```powershell
# Node 1
Invoke-RestMethod -Uri "http://localhost:6333"
# Node 2
Invoke-RestMethod -Uri "http://localhost:6343"
# Node 3
Invoke-RestMethod -Uri "http://localhost:6353"
# Node 4
Invoke-RestMethod -Uri "http://localhost:6363"
```

---

## BƯỚC 3: Tạo Collection với SHARD + REPLICA

```powershell
$body = @{
    vectors = @{
        dense = @{
            size = 384
            distance = "Cosine"
        }
    }
    shard_number = 4
    replication_factor = 2
    write_consistency_factor = 1
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_cluster" -ContentType "application/json" -Body $body
```

**Giải thích:**
- `shard_number = 4`: Data chia thành 4 phần, mỗi node giữ 1 shard primary (đúng như production)
- `replication_factor = 2`: Mỗi shard có 2 copies → mất 1 node vẫn hoạt động
- `write_consistency_factor = 1`: Ghi thành công nếu 1 replica xác nhận (nhanh hơn)

---

## BƯỚC 4: Kiểm tra phân bổ Shard

```powershell
$result = Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_cluster/cluster"
$result | ConvertTo-Json -Depth 10
```

→ Kỳ vọng: thấy 4 shards, mỗi shard có 2 replicas phân bổ trên 2 nodes khác nhau.

---

## BƯỚC 5: Tạo Payload Indexes

```powershell
$fields = @("doc_status", "domain", "department", "doc_type")

foreach ($field in $fields) {
    $body = @{
        field_name = $field
        field_schema = "keyword"
    } | ConvertTo-Json

    Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_cluster/index" -ContentType "application/json" -Body $body
    Write-Host "Created index: $field"
}
```

---

## BƯỚC 6: Upsert dữ liệu (dùng lại data cũ)

```powershell
$json1 = Get-Content -Raw -Path "..\sample_data\points_batch_01.json"
Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -ContentType "application/json" -Body $json1

$json2 = Get-Content -Raw -Path "..\sample_data\points_batch_02.json"
Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -ContentType "application/json" -Body $json2
```

Kiểm tra:
```powershell
(Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_cluster").result.points_count
```
→ Kỳ vọng: 12

---

## BƯỚC 7: Search từ các Node khác nhau

Mục tiêu: chứng minh search từ BẤT KỲ node nào đều trả kết quả (vì replica phân tán).

```powershell
$query = Get-Content -Raw -Path "..\queries\search_basic.json"

# Search qua Node 1 (port 6333)
Write-Host "=== SEARCH QUA NODE 1 ==="
Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5

# Search qua Node 2 (port 6343)
Write-Host "=== SEARCH QUA NODE 2 ==="
Invoke-RestMethod -Method Post -Uri "http://localhost:6343/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5

# Search qua Node 3 (port 6353)
Write-Host "=== SEARCH QUA NODE 3 ==="
Invoke-RestMethod -Method Post -Uri "http://localhost:6353/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5

# Search qua Node 4 (port 6363)
Write-Host "=== SEARCH QUA NODE 4 ==="
Invoke-RestMethod -Method Post -Uri "http://localhost:6363/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5
```

→ Kỳ vọng: cả 4 node trả kết quả **giống nhau** (cùng top 5, cùng score).

---

## BƯỚC 8: DEMO FAILOVER (mất 1 node)

Đây là phần quan trọng nhất – chứng minh cluster vẫn hoạt động khi mất 1 node.

### 8.1 Tắt Node 2
```powershell
docker stop qdrant-node2
Write-Host "Node 2 da tat!"
```

### 8.2 Kiểm tra cluster status
```powershell
Invoke-RestMethod -Uri "http://localhost:6333/cluster" | ConvertTo-Json -Depth 5
```
→ Kỳ vọng: cluster báo 1 peer unreachable nhưng vẫn hoạt động.

### 8.3 Search vẫn hoạt động (từ Node 1)
```powershell
$query = Get-Content -Raw -Path "..\queries\search_filter_domain.json"
Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5
```
→ Kỳ vọng: **Vẫn trả kết quả bình thường!** (nhờ replica trên các node còn lại)

### 8.4 Search từ Node 3 cũng OK
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:6353/collections/smart_search_cluster/points/query" -ContentType "application/json" -Body $query | ConvertTo-Json -Depth 5
```
→ Kỳ vọng: OK

### 8.5 Khôi phục Node 2
```powershell
docker start qdrant-node2
Start-Sleep -Seconds 5
Invoke-RestMethod -Uri "http://localhost:6333/cluster" | ConvertTo-Json -Depth 5
```
→ Kỳ vọng: Node 2 rejoin, cluster tự đồng bộ lại.

---

## BƯỚC 9: DEMO GHI KHI MẤT NODE

### 9.1 Tắt Node 3
```powershell
docker stop qdrant-node3
```

### 9.2 Upsert vẫn được (write_consistency_factor=1)
```powershell
$body = @{
    points = @(
        @{
            id = 100
            vector = @{ dense = @(1..384 | ForEach-Object { [math]::Round((Get-Random -Minimum -100 -Maximum 100) / 100, 4) }) }
            payload = @{
                document_id = "DOC-NEW"
                title = "Van ban moi upsert khi mat 1 node"
                domain = "cong_nghe"
                department = "CNTT"
                doc_type = "test"
                doc_status = "ACTIVE"
                text = "Day la van ban upsert khi node 3 da tat, chung minh cluster van ghi duoc."
            }
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Put -Uri "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -ContentType "application/json" -Body $body
```
→ Kỳ vọng: Ghi thành công (vì chỉ cần 1 replica xác nhận).

### 9.3 Khôi phục Node 3 → tự đồng bộ
```powershell
docker start qdrant-node3
Start-Sleep -Seconds 5

# Verify: search từ Node 3 tìm thấy point mới
$body2 = @{
    ids = @(100)
    with_payload = $true
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Method Post -Uri "http://localhost:6353/collections/smart_search_cluster/points" -ContentType "application/json" -Body $body2 | ConvertTo-Json -Depth 5
```
→ Kỳ vọng: Node 3 tự đồng bộ, tìm thấy point 100.

---

## BƯỚC 10: Kiểm tra Collection Cluster Info (chi tiết shard)

```powershell
$info = Invoke-RestMethod -Uri "http://localhost:6333/collections/smart_search_cluster/cluster"
$info | ConvertTo-Json -Depth 10
```

Kỳ vọng output có dạng:
```json
{
  "local_shards": [...],
  "remote_shards": [...],
  "shard_transfers": []
}
```

---

## BƯỚC 11: Cleanup

```powershell
cd D:\Qdrant\demo-local\cluster-demo
docker compose down -v
```

---

## TÓM TẮT DEMO CLUSTER

| Tính năng | Demo | Kết quả kỳ vọng |
|-----------|------|------------------|
| Cluster 4 nodes | 4 containers join cùng cluster | 4 peers online |
| Shard phân tán | 4 shards trên 4 nodes | Data chia đều |
| Replica | 2 copies mỗi shard | Redundancy |
| Search fan-out | Search từ bất kỳ node | Kết quả giống nhau |
| **Failover (đọc)** | Tắt 1 node → search vẫn OK | **HA hoạt động** |
| **Failover (ghi)** | Tắt 1 node → upsert vẫn OK | **Write resilience** |
| Auto-recovery | Bật lại node → tự đồng bộ | Cluster tự heal |

## SO SÁNH VỚI PRODUCTION

| Demo cluster (local) | Production |
|---|---|
| 4 containers trên 1 máy | 4 VMs riêng biệt |
| 1GB RAM/node | 32-48GB RAM/node |
| 4 shards | 4-8 shards |
| Replica=2 | Replica=2 |
| Không TLS | TLS + API key |
| 12 vectors | 8-10M vectors |
| Docker network | Private network + firewall |
