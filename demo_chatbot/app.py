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

from models import ChatRequest, UploadDocRequest, UnifiedResponse, ConfidenceInfo, SourceItem
from services.intent_classifier import classify_intent
from services.memory_service import get_history, add_message
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


@app.post("/chat", response_model=UnifiedResponse)
def chat(req: ChatRequest):
    """
    Endpoint chính: nhận câu hỏi → phân loại → xử lý → trả response thống nhất.
    """
    question = req.question.strip()
    conversation_id = req.conversation_id
    history = get_history(conversation_id)

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
        add_message(conversation_id, "user", question)
        add_message(conversation_id, "assistant", answer)

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

        add_message(conversation_id, "user", question)
        add_message(conversation_id, "assistant", f"Tra cứu STK: {len(results)} kết quả.")

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

    add_message(conversation_id, "user", question)
    add_message(conversation_id, "assistant", answer)

    return UnifiedResponse(
        type="knowledge",
        answer=answer,
        sources=sources,
        confidence=confidence,
    )


@app.post("/upload-doc")
def upload_doc(req: UploadDocRequest):
    """Upload tài liệu Markdown mới vào Qdrant (chunking + embed + index)."""
    # TODO: Implement với MarkdownTextSplitter + upsert
    # Tham khảo POC.py cho logic chunking
    return {"status": "pending", "message": "Chức năng đang phát triển. Dùng scripts/ingest_documents.py."}
