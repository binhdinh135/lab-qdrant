# HƯỚNG DẪN SỬ DỤNG - SMART SEARCH ASSISTANT POC

---

## Bước 1: Cài đặt môi trường

### 1.1 Yêu cầu hệ thống

- Windows 10/11
- Python 3.10+ (khuyến nghị 3.12)
- Docker Desktop (cho Qdrant)
- Ollama (cho LLM local)
- RAM tối thiểu 8GB (BGE-M3 + Qwen2.5 cần ~6GB RAM khi load)

### 1.2 Cài Ollama (LLM local, miễn phí)

1. Tải từ: https://ollama.com/download
2. Cài đặt xong, mở CMD chạy:

```cmd
ollama pull qwen2.5:7b
```

3. Verify Ollama đang chạy:

```cmd
curl.exe http://localhost:11434/api/tags
```

Kết quả phải thấy model `qwen2.5:7b` trong danh sách.

> **Lưu ý:** Ollama tự chạy background sau khi cài. Không cần start thủ công.

### 1.3 Tạo virtual environment (nếu chưa có)

```cmd
cd /d D:\Qdrant
python -m venv .venv
```

### 1.4 Cài đặt toàn bộ dependencies

```cmd
D:\Qdrant\.venv\Scripts\pip.exe install -r demo_chatbot\requirements.txt
D:\Qdrant\.venv\Scripts\pip.exe install langchain-ollama sentence-transformers
```

---

## Bước 2: Khởi động Qdrant (Docker)

### 2.1 Mở Docker Desktop

Đợi icon chuyển xanh (Docker Engine đang chạy).

### 2.2 Start Qdrant

```cmd
cd /d D:\Qdrant\demo-local
docker compose up -d
docker compose ps
```

Verify:

```cmd
curl.exe http://localhost:6333/healthz
```

Kết quả: `healthz` trả OK.

---

## Bước 3: Ingest tài liệu vào Qdrant

Script đọc tất cả file `.md` trong `data/documents/`, chunk theo Markdown headers, sinh embeddings (BGE-M3 + BM25), rồi upsert vào Qdrant.

```cmd
cd /d D:\Qdrant\demo_chatbot
D:\Qdrant\.venv\Scripts\python.exe scripts\ingest_documents.py
```

Output mong đợi:

```
============================================================
INGEST TÀI LIỆU VÀO QDRANT
============================================================
[1/5] Loading embedding models...
  ✅ Dense: BAAI/bge-m3 (1024 dims)
  ✅ Sparse: BM25
[2/5] Connecting Qdrant...
[3/5] Recreate collection 'internal_docs'...
  ✅ Collection created + indexes
[4/5] Reading documents from ...\data\documents...
  📄 QuyDinh_AnToanBaoMat.md: 4 chunks
  📄 QuyDinh_KYC.md: 5 chunks
  📄 QuyDinh_MoTaiKhoan.md: 4 chunks
  📄 QuyTrinh_CIF.md: 5 chunks
  📄 QuyTrinh_The.md: 4 chunks
  📄 QuyTrinh_TietKiem.md: 4 chunks
  Tổng: ~26 chunks
[5/5] Embedding + Upsert...
  ✅ Upserted XX points
============================================================
✅ HOÀN TẤT!
============================================================
```

> **Lần đầu chạy:** Model BGE-M3 sẽ download ~600MB. Các lần sau chạy nhanh (model đã cache).

---

## Bước 4: Chạy Backend (FastAPI)

```cmd
cd /d D:\Qdrant\demo_chatbot
D:\Qdrant\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000
```

Khi thấy:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

→ Backend đã sẵn sàng.

Verify:

```cmd
curl.exe http://localhost:8000/health
```

---

## Bước 5: Mở UI

Mở file `UI.html` trong browser (Chrome/Edge).

### Chuyển mode sang FastAPI Backend:

1. Ở góc trên phải, dropdown **Mode** → chọn **"FastAPI Backend (http://localhost:8000)"**
2. Status indicator chuyển xanh = kết nối OK

### Hoặc dùng mode Mock Simulator:

Nếu chưa chạy backend, UI vẫn hoạt động ở mode **"Browser Simulator (Standalone)"** với data mock sẵn.

---

## Bước 6: Test thử

### Qua UI:

Nhấn các nút kịch bản bên sidebar trái (KB1 → KB4).

### Qua curl:

```cmd
curl.exe -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"conversation_id\":\"test01\",\"question\":\"Quy trình mở CIF gồm những bước nào?\"}"
```

### Chạy test tự động (4 kịch bản):

```cmd
cd /d D:\Qdrant\demo_chatbot
D:\Qdrant\.venv\Scripts\python.exe scripts\test_scenarios.py
```

---

## Bước 7: Dừng hệ thống

```cmd
:: Dừng FastAPI: Ctrl+C trong terminal đang chạy uvicorn

:: Dừng Qdrant:
cd /d D:\Qdrant\demo-local
docker compose down
```

---

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `No module named 'xxx'` | Chưa cài package | `pip install xxx` |
| `ConnectError: 10061` | Qdrant chưa chạy | Bật Docker Desktop + `docker compose up -d` |
| `Model download...` chờ lâu | Download model lần đầu | Đợi (~600MB cho BGE-M3) |
| `CUDA out of memory` | GPU không đủ RAM | Tắt GPU: model tự dùng CPU |
| Port 8000 bị chiếm | App khác đang dùng | Đổi port: `--port 8001` |
| UI "FastAPI Offline" | Backend chưa chạy | Chạy uvicorn trước |

---

## Tóm tắt lệnh

```cmd
:: 1. Cài dependencies (chạy 1 lần)
D:\Qdrant\.venv\Scripts\pip.exe install -r demo_chatbot\requirements.txt
D:\Qdrant\.venv\Scripts\pip.exe install langchain-ollama sentence-transformers

:: 2. Cài Ollama + pull model (chạy 1 lần)
ollama pull qwen2.5:7b

:: 3. Start Qdrant (mỗi lần bật máy)
cd /d D:\Qdrant\demo-local
docker compose up -d

:: 4. Start backend (mở terminal mới)
cd /d D:\Qdrant\demo_chatbot
D:\Qdrant\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000

:: 5. Mở browser → http://127.0.0.1:8000
:: 6. Upload tài liệu .md qua nút "Nạp Tài Liệu" trên UI
:: 7. Chat hỏi đáp!
```

---

## Thứ tự khởi động (mỗi lần dùng)

```
1. Bật Docker Desktop (đợi xanh)
2. docker compose up -d (Qdrant)
3. Ollama tự chạy background (verify: curl localhost:11434/api/tags)
4. uvicorn app:app --port 8000 (Backend)
5. Mở http://127.0.0.1:8000 (UI)
6. Upload .md → Chat
```
