# GIAI ĐOẠN 2: QDRANT-CLIENT PYTHON

> Mục tiêu: Thành thạo `qdrant-client` — biết mỗi API Python tương ứng REST API nào.
> Sau project này, chuyển sang FastAPI / LangChain sẽ rất tự nhiên.

---

## Yêu cầu

```cmd
D:\Qdrant\.venv\Scripts\pip.exe install qdrant-client fastembed pydantic
```

**Qdrant đang chạy** tại `localhost:6333` (demo chính, không cần auth).

---

## Cấu trúc project

```
qdrant-client-demo/
├── README.md                       # File này
├── 01_connection.py                # Kết nối Qdrant (sync + async)
├── 02_collection.py                # Tạo / xóa / info collection
├── 03_upsert.py                    # Upsert points (đơn lẻ + batch)
├── 04_search.py                    # Search vector (dense)
├── 05_search_filter.py             # Search + filter payload
├── 06_hybrid_search.py             # Hybrid search (dense + sparse + RRF)
├── 07_scroll_get.py                # Scroll, get by ID, count
├── 08_update_delete.py             # Update payload, delete points
├── 09_auth.py                      # Kết nối với API Key / JWT
├── 10_fastapi_endpoint.py          # FastAPI endpoints (/search, /upsert)
├── models.py                       # Pydantic models (DTO)
└── config.py                       # Config chung
```

---

## Cách học

1. Đọc từng file theo thứ tự (01 → 10)
2. Mỗi file có:
   - Comment giải thích API Python tương ứng REST API nào
   - Code chạy được ngay
   - Output mong đợi
3. Chạy: `D:\Qdrant\.venv\Scripts\python.exe 01_connection.py`

---

## Mapping: Python Client ↔ REST API

| Python Client | REST API | Mô tả |
|--------------|----------|--------|
| `client.create_collection()` | PUT /collections/{name} | Tạo collection |
| `client.delete_collection()` | DELETE /collections/{name} | Xóa collection |
| `client.get_collection()` | GET /collections/{name} | Info collection |
| `client.upsert()` | PUT /collections/{name}/points | Upsert points |
| `client.search()` | POST /collections/{name}/points/search | Search |
| `client.query_points()` | POST /collections/{name}/points/query | Query (hybrid) |
| `client.scroll()` | POST /collections/{name}/points/scroll | Scroll |
| `client.retrieve()` | POST /collections/{name}/points | Get by IDs |
| `client.count()` | POST /collections/{name}/points/count | Count |
| `client.set_payload()` | POST /collections/{name}/points/payload | Update payload |
| `client.delete()` | POST /collections/{name}/points/delete | Delete points |
| `client.create_payload_index()` | PUT /collections/{name}/index | Create index |
