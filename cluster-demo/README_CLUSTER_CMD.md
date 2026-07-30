# KỊCH BẢN DEMO QDRANT CLUSTER - DÙNG CMD (WINDOWS)

> Phiên bản này là bản CMD của README_CLUSTER.md, dùng cho Command Prompt thay vì PowerShell.

---

## BƯỚC 1: Start cluster 4 nodes

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
docker compose up -d
docker compose ps
```

---

## BƯỚC 2: Kiểm tra cluster status

```cmd
curl.exe http://localhost:6333/cluster
curl.exe http://localhost:6333
curl.exe http://localhost:6343
curl.exe http://localhost:6353
curl.exe http://localhost:6363
```

---

## BƯỚC 3: Tạo Collection với SHARD + REPLICA

Tạo file JSON tạm:

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
> collection.json echo {"vectors":{"dense":{"size":384,"distance":"Cosine"}},"shard_number":4,"replication_factor":2,"write_consistency_factor":1}
```

Gửi request:

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster" -H "Content-Type: application/json" -d @collection.json
```

---

## BƯỚC 4: Kiểm tra phân bổ Shard

```cmd
curl.exe "http://localhost:6333/collections/smart_search_cluster/cluster"
```

---

## BƯỚC 5: Tạo Payload Indexes

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_status\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"domain\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"department\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_type\",\"field_schema\":\"keyword\"}"
```

---

## BƯỚC 6: Upsert dữ liệu (dùng lại data cũ)

```cmd
cd /d D:\Qdrant\demo-local
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_01.json
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_02.json
```

Kiểm tra số lượng points:

```cmd
curl.exe "http://localhost:6333/collections/smart_search_cluster"
```

---

## BƯỚC 7: Search từ các Node khác nhau

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6343/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6353/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6363/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
```

---

## BƯỚC 8: DEMO FAILOVER (mất 1 node)

Tắt Node 2:

```cmd
docker stop qdrant-node2
```

Search vẫn hoạt động:

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_filter_domain.json
```

Khôi phục Node 2:

```cmd
docker start qdrant-node2
```

---

## BƯỚC 9: DEMO GHI KHI MẤT NODE

Tắt Node 3:

```cmd
docker stop qdrant-node3
```

Upsert một điểm mới:

```cmd
> new_point.json echo {"points":[{"id":100,"vector":{"dense":[0.1,0.2,0.3]},"payload":{"document_id":"DOC-NEW","title":"Van ban moi upsert khi mat 1 node","domain":"cong_nghe","department":"CNTT","doc_type":"test","doc_status":"ACTIVE","text":"Day la van ban upsert khi node 3 da tat, chung minh cluster van ghi duoc."}}]}
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @new_point.json
```

Khôi phục Node 3:

```cmd
docker start qdrant-node3
```

---

## BƯỚC 10: Cleanup

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
docker compose down -v
```

---

## GHI CHÚ

Nếu bạn cần chạy theo hướng dẫn PowerShell, vẫn dùng file [README_CLUSTER.md](README_CLUSTER.md). Nếu cần chạy bằng CMD, dùng file này.
