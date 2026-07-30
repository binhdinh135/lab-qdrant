# KỊCH BẢN DEMO QDRANT - DÙNG CMD (WINDOWS)

> Phiên bản này dùng Command Prompt (cmd.exe) thay cho PowerShell. Các bước chạy tương tự như README chính nhưng sử dụng cú pháp CMD.

---

## BƯỚC 0: Khởi động Docker Desktop

Mở Docker Desktop rồi chờ icon chuyển màu xanh.

---

## BƯỚC 1: Start Qdrant

```cmd
cd /d D:\Qdrant\demo-local
docker compose up -d
docker compose ps
```

Mở browser:

```text
http://localhost:6333/dashboard
```

---

## BƯỚC 2: Health check

```cmd
curl.exe http://localhost:6333/healthz
curl.exe http://localhost:6333
```

---

## BƯỚC 3: Tạo Collection

Tạo file JSON tạm:

```cmd
cd /d D:\Qdrant\demo-local
> collection.json echo {"vectors":{"dense":{"size":384,"distance":"Cosine"}},"sparse_vectors":{"keywords":{}},"shard_number":1,"replication_factor":1}
```

Gửi request:

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo" -H "Content-Type: application/json" -d @collection.json
```

Kiểm tra:

```cmd
curl.exe "http://localhost:6333/collections/smart_search_demo"
```

---

## BƯỚC 4: Tạo Payload Indexes

```cmd
cd /d D:\Qdrant\demo-local
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_status\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/index" -H "Content-Type: application/json" -d "{\"field_name\":\"domain\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/index" -H "Content-Type: application/json" -d "{\"field_name\":\"department\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_type\",\"field_schema\":\"keyword\"}"
```

---

## BƯỚC 5: Sinh embedding cho câu hỏi (Query Embedding)

Luồng Hybrid Search bắt đầu từ câu hỏi của người dùng. Chạy script sau để sinh **Dense Embedding** và **Sparse Embedding** cho câu hỏi.

```cmd
cd /d D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\generate_query_embeddings.py
```

Sau khi chạy, chương trình sẽ hiển thị:

```text
Nhập câu hỏi tiếng Việt:
```

Ví dụ nhập:

```text
Hướng dẫn nghỉ phép
```

Nhấn **Enter**, script sẽ:

- Sinh **Dense Embedding** cho câu hỏi.
- Sinh **Sparse Embedding (BM25)** cho câu hỏi.
- Lưu kết quả vào file:

```text
queries\query_embeddings.json
```

File `query_embeddings.json` sẽ được sử dụng trực tiếp ở bước tiếp theo để thực hiện **Hybrid Search (Dense + Sparse + RRF)** trên Qdrant. Đây là body JSON chuẩn cho endpoint `/points/query`.

---

## BƯỚC 6: Tạo data points từ documents (offline ingestion)

```cmd
cd /d D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\generate_vectors.py
```

Đây là bước sinh dense + sparse embeddings cho documents để chuẩn bị upsert.

---

## BƯỚC 7: Upsert dữ liệu vào Qdrant

### 7.1 Cách nhanh: dùng script Python

```cmd
cd /d D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\upload_to_qdrant.py
```

### 7.2 Cách thủ công trên CMD: dùng curl để upsert trực tiếp

Nếu cần xóa collection cũ trước khi upload lại:

```cmd
curl.exe -X DELETE "http://localhost:6333/collections/smart_search_demo"
```

Sau đó tạo lại collection:

```cmd
cd /d D:\Qdrant\demo-local
> collection.json echo {"vectors":{"dense":{"size":384,"distance":"Cosine"}},"sparse_vectors":{"keywords":{}},"shard_number":1,"replication_factor":1}
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo" -H "Content-Type: application/json" -d @collection.json
```

Upsert batch 1:

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_01.json
```

Upsert batch 2:

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_demo/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_02.json
```

Kiểm tra số lượng points:

```cmd
curl.exe "http://localhost:6333/collections/smart_search_demo"
```

---

## BƯỚC 8: Hybrid Search (dùng câu hỏi đầu vào)

Sau khi đã có embedding cho câu hỏi ở Bước 5 và dữ liệu đã được upsert ở Bước 7, bạn phải dùng chính các embedding đó làm input cho query hybrid. Các ví dụ dưới đây là các mẫu search cơ bản; nếu cần đúng chuẩn hybrid search thì hãy dùng payload `prefetch + fusion = rrf` với dữ liệu từ `queries\query_embeddings.json`.

### 8.1 Search cơ bản

```cmd
cd /d D:\Qdrant\demo-local
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
```

### 8.2 Search + Filter theo domain = cong_nghe

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/query" -H "Content-Type: application/json" -d @queries\search_filter_domain.json
```

### 8.3 Search + Filter theo department = NHAN_SU

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/query" -H "Content-Type: application/json" -d @queries\search_filter_department.json
```

### 8.4 Search + Multi-filter

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/query" -H "Content-Type: application/json" -d @queries\search_multi_filter.json
```
### 8.5 Hybrid Search

```cmd
cd /d D:\Qdrant\demo-local
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/query" -H "Content-Type: application/json" -d @queries\query_embeddings.json
```
---

## BƯỚC 9: Scroll (liệt kê points)

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_demo/points/scroll" -H "Content-Type: application/json" -d "{\"limit\":5,\"with_payload\":true,\"with_vector\":false}"
```

---

## BƯỚC 10: Xóa Collection (cleanup)

```cmd
curl.exe -X DELETE "http://localhost:6333/collections/smart_search_demo"
```

---

## BƯỚC 11: Dừng Qdrant

```cmd
cd /d D:\Qdrant\demo-local
docker compose down
```

Data vẫn được giữ trong thư mục [demo-local/qdrant_storage](qdrant_storage) và sẽ sẵn sàng khi chạy lại docker compose up -d.

---

## BƯỚC 12: DEMO CLUSTER 4 NODE (CMD)

Nếu muốn thử đúng kiểu production-style cluster trên 1 máy Windows, có thể chạy thêm kịch bản sau bằng CMD.

### 10.1 Start cluster

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
docker compose up -d
docker compose ps
```

### 10.2 Kiểm tra cluster status

```cmd
curl.exe http://localhost:6333/cluster
curl.exe http://localhost:6333
curl.exe http://localhost:6343
curl.exe http://localhost:6353
curl.exe http://localhost:6363
```

### 10.3 Tạo collection cluster

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
> collection.json echo {"vectors":{"dense":{"size":384,"distance":"Cosine"}},"shard_number":4,"replication_factor":2,"write_consistency_factor":1}
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster" -H "Content-Type: application/json" -d @collection.json
```

### 10.4 Tạo payload indexes

```cmd
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_status\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"domain\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"department\",\"field_schema\":\"keyword\"}"
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/index" -H "Content-Type: application/json" -d "{\"field_name\":\"doc_type\",\"field_schema\":\"keyword\"}"
```

### 10.5 Upsert dữ liệu vào cluster

```cmd
cd /d D:\Qdrant\demo-local
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_01.json
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @sample_data\points_batch_02.json
```

### 10.6 Test search từ các node khác nhau

```cmd
curl.exe -X POST "http://localhost:6333/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6343/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6353/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
curl.exe -X POST "http://localhost:6363/collections/smart_search_cluster/points/query" -H "Content-Type: application/json" -d @queries\search_basic.json
```

### 10.7 Test failover khi tắt node

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

Tắt Node 3 rồi thử upsert một điểm mới:

```cmd
docker stop qdrant-node3
> new_point.json echo {"points":[{"id":100,"vector":{"dense":[0.1,0.2,0.3]},"payload":{"document_id":"DOC-NEW","title":"Van ban moi upsert khi mat 1 node","domain":"cong_nghe","department":"CNTT","doc_type":"test","doc_status":"ACTIVE","text":"Day la van ban upsert khi node 3 da tat, chung minh cluster van ghi duoc."}}]}
curl.exe -X PUT "http://localhost:6333/collections/smart_search_cluster/points?wait=true" -H "Content-Type: application/json" -d @new_point.json
docker start qdrant-node3
```

### 10.8 Cleanup

```cmd
cd /d D:\Qdrant\demo-local\cluster-demo
docker compose down -v
```
