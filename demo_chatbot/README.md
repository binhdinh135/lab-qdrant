# DEMO/POC TRỢ LÝ SMART SEARCH NỘI BỘ

> **PIC:** Dũng & Tuấn  
> **Mục tiêu:** POC trợ lý hỏi-đáp tiếng Việt trên kho tài liệu nội bộ (quy chế/quy trình)  
> **Stack:** Qdrant + FastAPI + LangChain + Fastembed + Conversation Memory  

---

## Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI (UI.html)                            │
│  Browser Chat Interface (Tailwind CSS)                          │
│  Mode: Mock Simulator (standalone) | FastAPI Backend            │
└────────────────────────────┬────────────────────────────────────┘
                             │ POST /chat, /upload-doc
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (app.py)                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Intent Classifier  →  "knowledge" | "operation" | "chitchat"│
│  2. RAG Pipeline       →  Embed query → Qdrant search → LLM    │
│  3. Account Lookup     →  Fuzzy match STK (tool API)            │
│  4. Conversation Memory →  Session-based history (RAM)          │
│  5. Response Formatter →  answer + sources + confidence         │
└──────────┬──────────────────────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────┐     ┌─────────────────────────────────────┐
│  Qdrant Vector DB   │     │  LLM (OpenAI / Ollama / Fake)       │
│  - Collection:      │     │  - Prompt: system + context + history│
│    internal_docs    │     │  - Output: JSON answer + citations   │
│  - Dense: 384 dims  │     └─────────────────────────────────────┘
│  - Sparse: BM25     │
│  - Payload indexes  │
└─────────────────────┘
```

---

## Cấu trúc folder

```
demo_chatbot/
├── README.md                   # File này - tổng quan kiến trúc
├── UI.html                     # Frontend chat (standalone + API mode)
├── app.py                      # FastAPI backend chính (production-ready)
├── config.py                   # Config (Qdrant URL, LLM, models)
├── models.py                   # Pydantic schemas (request/response)
├── services/
│   ├── intent_classifier.py    # Phân loại intent (knowledge/operation/chitchat)
│   ├── rag_service.py          # RAG pipeline (embed → search → LLM → format)
│   ├── account_service.py      # Tra cứu STK (mock hoặc API thật)
│   └── memory_service.py       # Conversation memory (session-based)
├── data/
│   ├── documents/              # 10 tài liệu Markdown nội bộ
│   │   ├── QuyTrinh_CIF.md
│   │   ├── QuyDinh_KYC.md
│   │   ├── QuyTrinh_The.md
│   │   ├── QuyDinh_MoTaiKhoan.md
│   │   ├── QuyTrinh_TietKiem.md
│   │   ├── QuyDinh_AnToanBaoMat.md
│   │   └── ...
│   └── accounts_mock.json      # Mock database STK
├── scripts/
│   ├── ingest_documents.py     # Script chunking + embed + upsert docs vào Qdrant
│   └── test_scenarios.py       # Script chạy 4 kịch bản nghiệm thu tự động
├── POC.py                      # (Legacy) File POC ban đầu - reference
└── requirements.txt            # Dependencies
```

---

## 4 Kịch bản nghiệm thu

| # | Kịch bản | Input mẫu | Output mong đợi |
|---|----------|-----------|-----------------|
| 1 | Trả lời có trích dẫn | "Quy trình mở CIF gồm những bước nào?" | Trả lời 5 bước + trích dẫn QuyTrinh_CIF.md Mục 3.2 + confidence ≥ 0.85 |
| 2 | Tra cứu STK gần đúng | "1234567" | Gợi ý 2 STK khớp + điểm tin cậy + lý do |
| 3 | Hỏi nối tiếp (memory) | Hỏi CIF → "Thời gian xử lý mất bao lâu?" | Hiểu ngữ cảnh CIF → trả lời 15-30 phút |
| 4 | eKYC knowledge | "Đối tượng nào được áp dụng eKYC?" | KH cá nhân + Mobile Banking + trích dẫn |

---

## Cách chạy

### 1. Cài dependencies

```cmd
D:\Qdrant\.venv\Scripts\pip.exe install fastapi uvicorn langchain langchain-community qdrant-client fastembed pydantic
```

### 2. Khởi động Qdrant (đã có sẵn)

```cmd
cd /d D:\Qdrant\demo-local
docker compose up -d
```

### 3. Ingest tài liệu vào Qdrant

```cmd
cd /d D:\Qdrant\demo_chatbot
D:\Qdrant\.venv\Scripts\python.exe scripts\ingest_documents.py
```

### 4. Chạy backend

```cmd
D:\Qdrant\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000
```

### 5. Mở UI

Mở `UI.html` trong browser → chuyển mode sang "FastAPI Backend".

### 6. Test kịch bản tự động

```cmd
D:\Qdrant\.venv\Scripts\python.exe scripts\test_scenarios.py
```

---

## Response format thống nhất

Mọi phản hồi từ `/chat` đều theo cấu trúc:

```json
{
  "type": "knowledge | operation | chitchat",
  "answer": "Nội dung trả lời...",
  "sources": [
    {"document": "QuyTrinh_CIF.md", "section": "3.2", "content_snippet": "..."}
  ],
  "results": [
    {"account": "1234567890", "name": "NGUYEN VAN A", "score": 0.96, "reason": "Khớp tiền tố"}
  ],
  "confidence": {"score": 0.94, "level": "High"}
}
```

---

## Mapping với kiến thức đã học

| Component | Kiến thức Giai đoạn 1-2 đã demo |
|-----------|--------------------------------|
| Qdrant Collection | `02_collection.py` - tạo dense + sparse vectors |
| Upsert documents | `03_upsert.py` - embed + batch upsert |
| Search (RAG retrieval) | `06_hybrid_search.py` - dense + sparse + RRF |
| Filter (department) | `05_search_filter.py` - filter payload |
| Auth (JWT per-team) | `auth-demo/kich-ban-2` - JWT per collection |
| FastAPI integration | `10_fastapi_endpoint.py` - /search, /upsert |
| Pydantic models | `models.py` - request/response validation |
