# DEMO PHÂN QUYỀN QDRANT (Authorization / RBAC)

> Folder này chứa toàn bộ kịch bản test phân quyền trên Qdrant, từ cơ bản đến nâng cao.
> Mỗi kịch bản **tự đủ (self-contained)**: bắt đầu từ docker compose → sinh data → sinh query → test.

---

## Cấu trúc thư mục

```
auth-demo/
├── docker-compose.yml              # Qdrant với API Key + JWT (dùng chung)
├── README.md                       # File này
├── scripts/
│   ├── setup_collection.py         # Tạo collection + upload data (dùng chung KB1, KB1B)
│   └── generate_query.py           # Sinh query embeddings (dùng chung)
├── queries/                        # Output của generate_query.py (auto-generated)
│   ├── query_dense.json
│   └── query_hybrid.json
├── kich-ban-1-api-key/             # KB1: Admin vs Read-only vs No Key
│   └── README_KB1.md
├── kich-ban-1b-readonly-key/       # KB1B: Read-only Key chi tiết (16 test cases)
│   └── README_KB1B.md
├── kich-ban-2-jwt-collection/      # KB2: JWT phân quyền theo collection
│   ├── README_KB2.md
│   ├── generate_tokens.py          # Tạo JWT token HR/IT
│   └── setup_data.py              # Sinh embeddings + upload cho hr_docs/it_docs
├── kich-ban-3-jwt-multitenant/     # KB3: JWT + payload filter (multi-tenant)
│   ├── README_KB3.md
│   ├── generate_tokens.py          # Tạo JWT token 3 phòng ban
│   └── setup_data.py              # Sinh embeddings + upload cho company_docs
└── qdrant_storage/                 # Data (auto-generated khi chạy)
```

---

## Yêu cầu

- Docker Desktop đang chạy
- Python virtualenv đã cài: `fastembed`, `pyjwt`
- Đã chạy `generate_vectors.py` ít nhất 1 lần (cho KB1, KB1B)

```cmd
D:\Qdrant\.venv\Scripts\pip.exe install fastembed pyjwt
```

---

## Thông tin cấu hình chung

| Tham số | Giá trị |
|---------|---------|
| Port REST API | `6380` (tránh conflict với demo chính 6333) |
| Port gRPC | `6381` |
| Admin API Key | `admin-secret-key-2024` |
| Read-only API Key | `readonly-key-2024` |
| JWT RBAC | Enabled |

---

## Flow chung mỗi kịch bản

```
1. docker compose up -d          ← Khởi động Qdrant (có auth)
2. Sinh data (Python script)     ← Generate embeddings + upsert
3. Sinh query (Python script)    ← Generate query embeddings
4. Test phân quyền (curl)        ← Chạy từng test case
5. docker compose down           ← Cleanup
```

---

## Chạy từng kịch bản

| # | Kịch bản | Mô tả | Độ khó |
|---|----------|--------|--------|
| 1 | [API Key](kich-ban-1-api-key/README_KB1.md) | Admin vs Read-only vs Anonymous | ⭐ Cơ bản |
| 1B | [Read-only chi tiết](kich-ban-1b-readonly-key/README_KB1B.md) | 16 test cases đọc/ghi | ⭐ Cơ bản |
| 2 | [JWT per-Collection](kich-ban-2-jwt-collection/README_KB2.md) | Token giới hạn theo collection | ⭐⭐ Trung bình |
| 3 | [JWT Multi-tenant](kich-ban-3-jwt-multitenant/README_KB3.md) | Payload filter tự động | ⭐⭐⭐ Nâng cao |

---

## Quick Start (chạy nhanh KB1)

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
docker compose up -d

:: Sinh data
cd /d D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe sample_data\generate_vectors.py
cd /d D:\Qdrant\demo-local\auth-demo
D:\Qdrant\.venv\Scripts\python.exe scripts\setup_collection.py

:: Sinh query
D:\Qdrant\.venv\Scripts\python.exe scripts\generate_query.py

:: Test nhanh
curl.exe http://localhost:6380/collections
curl.exe "http://localhost:6380/collections" -H "api-key: readonly-key-2024"
curl.exe "http://localhost:6380/collections" -H "api-key: admin-secret-key-2024"
```

---

## Cleanup toàn bộ

```cmd
cd /d D:\Qdrant\demo-local\auth-demo
docker compose down -v
```
