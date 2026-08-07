# Search Service

Module tìm kiếm trên Qdrant — tầng trên, không liên quan đến RBAC/phân quyền.

## Chức năng

- **Semantic search** — tìm kiếm vector similarity
- **Keyword search** — full-text search trên payload
- **Hybrid search** — kết hợp vector + keyword với RRF fusion
- **ACL filtering** — lọc kết quả dựa trên metadata (department, owner, tags...)
- **Multi-collection search** — tìm đồng thời trên nhiều collections

## Cách chạy

```bash
cd search-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## Kiến trúc

```
search-service/
├── app.py              # FastAPI entry point (port 8001)
├── config.py           # Env vars
├── models/
│   └── schemas.py      # Request/Response models
├── services/
│   ├── vector_search.py    # Semantic search
│   ├── keyword_search.py   # Full-text search
│   ├── hybrid_search.py    # Hybrid + RRF fusion
│   └── acl_filter.py       # ACL metadata filter builder
├── requirements.txt
└── .env.example
```

## Quan hệ với Backend RBAC

Search Service KHÔNG xử lý phân quyền. Nó nhận Qdrant JWT token
từ client (đã lấy qua backend RBAC) và gửi thẳng token đó khi
gọi Qdrant. Qdrant tự enforce quyền dựa trên token.

```
Client → login Backend RBAC → nhận qdrant_token
Client → gọi Search Service + Bearer qdrant_token → Qdrant enforce
```
