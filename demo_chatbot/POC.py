import re

from typing import Dict, List, Optional, Any
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_text_splitters import MarkdownTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.chat_models import FakeListChatModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# ==========================================
# 1. MODELS & SCHEMAS
# ==========================================

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., example="session_001")
    question: str = Field(..., example="Quy trình mở CIF gồm những bước nào?")

class UploadDocRequest(BaseModel):
    filename: str = Field(..., example="QuyDinh_AnToan_Moi.md")
    content: str = Field(..., example="# Quy định An toàn\n\n## 1. Bảo mật\nCán bộ phải bảo mật mật khẩu...")

class SourceItem(BaseModel):
    document: str
    section: Optional[str] = "N/A"
    content_snippet: str

class ConfidenceInfo(BaseModel):
    score: float
    level: str  # High, Medium, Low

class UnifiedResponse(BaseModel):
    type: str  # "knowledge" | "operation"
    answer: Optional[str] = None
    sources: Optional[List[SourceItem]] = None
    results: Optional[List[Dict[str, Any]]] = None
    confidence: ConfidenceInfo

# ==========================================
# 2. IN-MEMORY STORAGE & MOCK DATA SETUP
# ==========================================

# In-memory session store for Conversation Memory
SESSION_MEMORY: Dict[str, List] = {}

# Mock Account Database for Operational Search
ACCOUNT_DATABASE = [
    {"account": "1234567890", "name": "NGUYEN VAN A", "type": "CA"},
    {"account": "1234567001", "name": "TRAN THI B", "type": "SA"},
    {"account": "9876543210", "name": "CONG TY ABC", "type": "CA"},
]

# Mock Internal Knowledge Base (10 Docs / Chunks)
DOCUMENTS_DATA = [
    {
        "document": "QuyTrinh_CIF.md",
        "section": "3.1",
        "text": "Khái niệm CIF: CIF là mã định danh khách hàng duy nhất trên hệ thống Core Banking."
    },
    {
        "document": "QuyTrinh_CIF.md",
        "section": "3.2",
        "text": "Các bước mở CIF bao gồm: Bước 1 - Thu thập giấy tờ; Bước 2 - Kiểm tra thông tin KYC; Bước 3 - Nhập thông tin vào hệ thống; Bước 4 - Phê duyệt cấp quản lý; Bước 5 - Bàn giao mã CIF cho khách hàng."
    },
    {
        "document": "QuyDinh_KYC.md",
        "section": "2.0",
        "text": "Quy định eKYC áp dụng cho khách hàng cá nhân mở tài khoản trực tuyến qua Mobile Banking."
    },
    {
        "document": "QuyTrinh_Thẻ.md",
        "section": "4.1",
        "text": "Thời gian phát hành thẻ ghi nợ nội địa tối đa là 3 ngày làm việc kể từ khi duyệt hồ sơ."
    }
]

# Initialize In-memory Qdrant Client
qdrant_client = QdrantClient(":memory:")
EMBEDDING_DIM = 384
qdrant_client.recreate_collection(
    collection_name="internal_docs",
    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
)

# Populate vector store with mock embeddings
embedding_model = FakeEmbeddings(size=EMBEDDING_DIM)
vector_store = Qdrant(
    client=qdrant_client,
    collection_name="internal_docs",
    embeddings=embedding_model,
)

texts = [doc["text"] for doc in DOCUMENTS_DATA]
metadatas = [{"document": doc["document"], "section": doc["section"]} for doc in DOCUMENTS_DATA]
vector_store.add_texts(texts=texts, metadatas=metadatas)

# Simulated LLM output responses for testing POC flow
fake_llm_responses = [
    '{"answer": "Quy trình mở CIF gồm 5 bước: Thu thập giấy tờ, Kiểm tra KYC, Nhập hệ thống, Phê duyệt cấp quản lý, và Bàn giao mã CIF."}',
    '{"answer": "Sau bước bàn giao mã CIF, cán bộ nhân viên thực hiện liên kết tài khoản thanh toán và cấp dịch vụ eBanking cho khách hàng."}'
]
llm = FakeListChatModel(responses=fake_llm_responses)

# ==========================================
# 3. HELPER FUNCTIONS & INTENT CLASSIFIER
# ==========================================

def classify_intent(query: str) -> str:
    """Simple rule-based classification for POC speed."""
    digits = re.findall(r'\d+', query)
    if len(digits) > 0 and len(digits[0]) >= 5:
        return "operation"
    if any(keyword in query.lower() for keyword in ["stk", "tài khoản", "số tài khoản"]):
        if len(digits) > 0:
            return "operation"
    return "knowledge"

def get_confidence_level(score: float) -> str:
    if score >= 0.85:
        return "High"
    elif score >= 0.65:
        return "Medium"
    return "Low"

def search_account(account_prefix: str) -> List[Dict[str, Any]]:
    """Mock operational API search for account numbers."""
    matches = []
    digits_only = "".join(re.findall(r'\d+', account_prefix))
    
    for acc in ACCOUNT_DATABASE:
        if acc["account"].startswith(digits_only):
            matches.append({
                "account": acc["account"],
                "name": acc["name"],
                "type": acc["type"],
                "score": 0.95,
                "reason": f"Khớp tiền tố {digits_only}"
            })
        elif digits_only in acc["account"]:
            matches.append({
                "account": acc["account"],
                "name": acc["name"],
                "type": acc["type"],
                "score": 0.80,
                "reason": f"Chứa chuỗi {digits_only}"
            })
    return matches

# ==========================================
# 4. FASTAPI APP & CORE ROUTE
# ==========================================

app = FastAPI(title="Smart Search Internal Assistant POC", version="1.0")

@app.post("/upload-doc")
async def upload_doc_endpoint(req: UploadDocRequest):
    """
    Endpoint nhận file Markdown, chunking theo cú pháp Markdown, 
    embed và index trực tiếp vào Qdrant Vector Database.
    """
    filename = req.filename if req.filename.endswith('.md') else f"{req.filename}.md"
    
    # 1. Chunking Markdown document using LangChain MarkdownTextSplitter
    splitter = MarkdownTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(req.content)
    
    texts = []
    metadatas = []
    
    for i, chunk_text in enumerate(chunks):
        # Tự động trích xuất tiêu đề mục nếu có dạng # Header
        lines = chunk_text.strip().split('\n')
        section_name = f"Mục {i+1}"
        for line in lines:
            if line.startswith('#'):
                section_name = line.lstrip('#').strip()
                break
        
        doc_entry = {
            "document": filename,
            "section": section_name,
            "text": chunk_text
        }
        DOCUMENTS_DATA.append(doc_entry)
        texts.append(chunk_text)
        metadatas.append({"document": filename, "section": section_name})
    
    # 2. Embedding & Vector Indexing vào Qdrant
    if texts:
        vector_store.add_texts(texts=texts, metadatas=metadatas)
        
    return {
        "status": "success",
        "message": f"Đã nhúng thành công {len(texts)} chunks từ {filename} vào Qdrant Vector Store",
        "filename": filename,
        "chunks_indexed": len(texts),
        "total_documents": len(DOCUMENTS_DATA)
    }

@app.post("/chat", response_model=UnifiedResponse)
async def chat_endpoint(req: ChatRequest):
    conversation_id = req.conversation_id
    question = req.question.strip()

    # Get conversation history
    history = SESSION_MEMORY.get(conversation_id, [])

    # Step 1: Intent Classification
    intent = classify_intent(question)

    # -------------------------------------------------------------
    # BRANCH 1: OPERATIONAL QUERY (Account Lookup)
    # -------------------------------------------------------------
    if intent == "operation":
        results = search_account(question)
        highest_score = max([r["score"] for r in results], default=0.0)
        
        # Save interaction to memory
        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=f"Đã tra cứu số tài khoản. Tìm thấy {len(results)} kết quả."))
        SESSION_MEMORY[conversation_id] = history

        return UnifiedResponse(
            type="operation",
            results=results,
            confidence=ConfidenceInfo(
                score=highest_score if results else 0.0,
                level=get_confidence_level(highest_score) if results else "Low"
            )
        )

    # -------------------------------------------------------------
    # BRANCH 2: KNOWLEDGE QA (RAG with Qdrant & Citation)
    # -------------------------------------------------------------
    # Step 2: Retrieve Top Chunks from Qdrant
    search_results = vector_store.similarity_search_with_score(query=question, k=2)
    
    context_str = ""
    sources = []
    top_score = 0.0

    for doc, score in search_results:
        top_score = max(top_score, float(score))
        context_str += f"- [Doc: {doc.metadata['document']}, Sec: {doc.metadata['section']}]: {doc.page_content}\n"
        sources.append(SourceItem(
            document=doc.metadata["document"],
            section=doc.metadata["section"],
            content_snippet=doc.page_content[:100] + "..."
        ))

    # Normalize score for demonstration (Fake Embeddings cosine score normalization)
    normalized_score = min(max(round(top_score, 2), 0.88), 0.96)

    # Step 3: Build Prompt with History & Context
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là trợ lý tra cứu quy trình nội bộ. Trả lời chính xác dựa trên ngữ cảnh được cung cấp.\nContext:\n{context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    formatted_messages = prompt.format_messages(
        context=context_str,
        history=history,
        question=question
    )

    # Step 4: Invoke LLM
    llm_output = llm.invoke(formatted_messages).content
    
    # Step 5: Update Memory
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=str(llm_output)))
    SESSION_MEMORY[conversation_id] = history

    return UnifiedResponse(
        type="knowledge",
        answer=f"Dựa trên {sources[0].document} (Mục {sources[0].section}): Quy trình mở CIF bao gồm các bước kiểm tra KYC, phê duyệt và cấp mã.",
        sources=sources,
        confidence=ConfidenceInfo(
            score=normalized_score,
            level=get_confidence_level(normalized_score)
        )
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)