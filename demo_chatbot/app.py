"""
Smart Search Internal Assistant - FastAPI Backend.

Endpoints:
  POST /chat        → Hỏi-đáp (auto phân loại intent)
  POST /upload-doc  → Upload tài liệu Markdown vào Qdrant
  GET  /health      → Health check

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe -m uvicorn app:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from models import ChatRequest, UploadDocRequest, UnifiedResponse, ConfidenceInfo, SourceItem
from services.intent_classifier import classify_intent
from services.memory_service import get_messages, add_user_message, add_ai_message
from services.account_service import search_account
from services.rag_service import retrieve_and_answer
from config import QDRANT_URL, COLLECTION_NAME


app = FastAPI(
    title="Smart Search Internal Assistant",
    description="POC Trợ lý hỏi-đáp tiếng Việt trên kho tài liệu nội bộ",
    version="1.0.0",
)

# CORS cho UI.html mở từ file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "qdrant": QDRANT_URL, "collection": COLLECTION_NAME}


@app.post("/verify-account")
def verify_account(data: dict):
    """
    Xác thực số tài khoản trước khi cho phép chat.
    Input: {"account": "1234567890"}
    Output: {"valid": true, "name": "NGUYEN VAN A", "type": "CA"} hoặc {"valid": false}
    """
    account_number = data.get("account", "").strip()
    
    # Load accounts
    import json
    from pathlib import Path
    accounts_path = Path(__file__).parent / "data" / "accounts_mock.json"
    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    
    for acc in accounts:
        if acc["account"] == account_number:
            return {"valid": True, "name": acc["name"], "type": acc["type"], "account": acc["account"]}
    
    return {"valid": False, "message": "Số tài khoản không tồn tại trong hệ thống."}


@app.get("/")
def serve_ui():
    """Serve UI.html khi truy cập http://localhost:8000/"""
    ui_path = Path(__file__).parent / "UI.html"
    return FileResponse(ui_path, media_type="text/html")


@app.post("/chat", response_model=UnifiedResponse)
def chat(req: ChatRequest):
    """
    Endpoint chính: nhận câu hỏi → phân loại → xử lý → trả response thống nhất.
    """
    question = req.question.strip()
    conversation_id = req.conversation_id
    history = get_messages(conversation_id)

    # Step 1: Phân loại intent
    intent = classify_intent(question)

    # ─── CHITCHAT ───
    if intent == "chitchat":
        answer = (
            "Xin chào! Tôi là Trợ lý Smart Search Nội bộ. Tôi có thể hỗ trợ bạn:\n\n"
            "1. Tra cứu Quy trình & Quy chế nội bộ (CIF, eKYC, Thẻ, Tiết kiệm...)\n"
            "2. Tra cứu Số tài khoản tác nghiệp gần đúng.\n\n"
            "Bạn cần hỗ trợ gì ạ?"
        )
        add_user_message(conversation_id, question)
        add_ai_message(conversation_id, answer)

        return UnifiedResponse(
            type="chitchat",
            answer=answer,
            sources=[],
            confidence=ConfidenceInfo(score=1.0, level="High"),
        )

    # ─── OPERATION (Account Lookup) ───
    if intent == "operation":
        results = search_account(question)
        highest_score = max([r["score"] for r in results], default=0.0)

        add_user_message(conversation_id, question)
        add_ai_message(conversation_id, f"Tra cứu STK: {len(results)} kết quả.")

        return UnifiedResponse(
            type="operation",
            results=results,
            confidence=ConfidenceInfo(
                score=highest_score,
                level="High" if highest_score >= 0.9 else "Medium" if highest_score >= 0.7 else "Low",
            ),
        )

    # ─── KNOWLEDGE (RAG) ───
    answer, sources, confidence = retrieve_and_answer(question, history)

    add_user_message(conversation_id, question)
    add_ai_message(conversation_id, answer)

    return UnifiedResponse(
        type="knowledge",
        answer=answer,
        sources=sources,
        confidence=confidence,
    )


@app.post("/upload-doc")
def upload_doc(req: UploadDocRequest):
    """
    Upload tài liệu Markdown → chunking → embedding (BGE-M3 + BM25) → upsert vào Qdrant.
    
    Pipeline:
      1. Parse nội dung Markdown
      2. Chunk theo headers (##)
      3. Sinh dense embedding (BGE-M3, 1024 dims) + sparse embedding (BM25)
      4. Upsert vào collection internal_docs
    """
    from qdrant_client.models import PointStruct, SparseVector
    from services.rag_service import _get_client, _get_dense_model, _get_sparse_model
    from config import COLLECTION_NAME

    filename = req.filename if req.filename.endswith(".md") else f"{req.filename}.md"
    content = req.content

    # 1. Chunking theo Markdown headers
    chunks = []
    current_section = "Intro"
    current_text = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_text:
                text = "\n".join(current_text).strip()
                if text:
                    chunks.append({"document": filename, "section": current_section, "text": text})
            current_section = line.lstrip("#").strip()
            current_text = []
        elif line.startswith("# "):
            current_section = line.lstrip("#").strip()
        else:
            current_text.append(line)

    if current_text:
        text = "\n".join(current_text).strip()
        if text:
            chunks.append({"document": filename, "section": current_section, "text": text})

    if not chunks:
        return {"status": "error", "message": "Không tìm thấy nội dung trong file."}

    # 2. Sinh embeddings
    client = _get_client()
    dense_model = _get_dense_model()
    sparse_model = _get_sparse_model()

    texts = [f"{c['document']} - {c['section']}: {c['text']}" for c in chunks]
    dense_vectors = dense_model.encode(texts, normalize_embeddings=True)
    sparse_vectors = list(sparse_model.embed(texts))

    # 3. Tạo point ID (offset từ count hiện tại)
    current_count = client.count(collection_name=COLLECTION_NAME, exact=True).count
    
    points = []
    for i, chunk in enumerate(chunks):
        point_id = current_count + i + 1
        points.append(PointStruct(
            id=point_id,
            vector={
                "dense": dense_vectors[i].tolist(),
                "keywords": SparseVector(
                    indices=sparse_vectors[i].indices.tolist(),
                    values=sparse_vectors[i].values.tolist(),
                ),
            },
            payload=chunk,
        ))

    # 4. Upsert vào Qdrant
    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    return {
        "status": "success",
        "message": f"Đã nạp {len(chunks)} chunks từ {filename} vào Qdrant",
        "filename": filename,
        "chunks_indexed": len(chunks),
        "total_points": current_count + len(chunks),
    }
