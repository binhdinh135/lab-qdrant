"""
RAG Service: Retrieval-Augmented Generation pipeline.

Luồng:
  1. Embed câu hỏi (dense + sparse)
  2. Hybrid Search trên Qdrant (dense + sparse + RRF)
  3. Build prompt (system + context + history + question)
  4. Gọi LLM → sinh câu trả lời
  5. Format response (answer + sources + confidence)
"""

from typing import List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector, Prefetch, FusionQuery, Fusion
from fastembed import TextEmbedding, SparseTextEmbedding
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DENSE_MODEL_NAME, SPARSE_MODEL_NAME, LLM_PROVIDER,
)
from models import SourceItem, ConfidenceInfo


# === Lazy-loaded globals ===
_client: QdrantClient = None
_dense_model: TextEmbedding = None
_sparse_model: SparseTextEmbedding = None
_llm = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _client


def _get_dense_model() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        _dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    return _dense_model


def _get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
    return _sparse_model


def _get_llm():
    global _llm
    if _llm is None:
        if LLM_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI
            from config import OPENAI_API_KEY
            _llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
        elif LLM_PROVIDER == "ollama":
            from langchain_ollama import ChatOllama
            from config import OLLAMA_MODEL, OLLAMA_BASE_URL
            _llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        else:
            # Fake LLM cho demo (không cần API key)
            from langchain_community.chat_models import FakeListChatModel
            _llm = FakeListChatModel(responses=[
                "Dựa trên tài liệu nội bộ, quy trình bao gồm các bước được mô tả trong nguồn trích dẫn bên dưới."
            ])
    return _llm


# === RAG Prompt ===
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là trợ lý tra cứu quy trình nội bộ ngân hàng. Quy tắc:
1. Trả lời chính xác dựa trên ngữ cảnh (context) được cung cấp.
2. Nếu context không đủ thông tin, nói rõ "Tôi chưa tìm thấy thông tin này trong kho tài liệu."
3. Luôn nêu tên tài liệu và mục (section) đã tham chiếu.
4. Trả lời ngắn gọn, đúng trọng tâm, bằng tiếng Việt.

Context:
{context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])


def retrieve_and_answer(
    question: str,
    history: List[BaseMessage],
    top_k: int = 3,
) -> Tuple[str, List[SourceItem], ConfidenceInfo]:
    """
    Thực hiện RAG pipeline đầy đủ.
    
    Returns: (answer, sources, confidence)
    """
    client = _get_client()
    dense_model = _get_dense_model()
    sparse_model = _get_sparse_model()
    llm = _get_llm()

    # 1. Embed query
    query_dense = list(dense_model.embed([question]))[0].tolist()
    query_sparse_raw = list(sparse_model.embed([question]))[0]
    query_sparse = SparseVector(
        indices=query_sparse_raw.indices.tolist(),
        values=query_sparse_raw.values.tolist(),
    )

    # 2. Hybrid Search (dense + sparse + RRF)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=query_dense, using="dense", limit=20),
            Prefetch(query=query_sparse, using="keywords", limit=20),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
        with_payload=True,
    )

    # 3. Build context + sources
    context_parts = []
    sources = []
    top_score = 0.0

    for point in results.points:
        top_score = max(top_score, point.score)
        doc_name = point.payload.get("document", point.payload.get("document_id", "Unknown"))
        section = point.payload.get("section", "N/A")
        text = point.payload.get("text", point.payload.get("page_content", ""))

        context_parts.append(f"[{doc_name}, Mục {section}]: {text}")
        sources.append(SourceItem(
            document=doc_name,
            section=section,
            content_snippet=text[:150] + "..." if len(text) > 150 else text,
        ))

    context_str = "\n".join(context_parts) if context_parts else "Không tìm thấy tài liệu liên quan."

    # 4. Build prompt + call LLM
    messages = RAG_PROMPT.format_messages(
        context=context_str,
        history=history,
        question=question,
    )
    llm_output = llm.invoke(messages).content

    # 5. Confidence
    confidence_score = round(top_score, 2) if top_score > 0 else 0.0
    # Normalize RRF score (max=1.0 khi perfect match)
    if confidence_score > 0.8:
        level = "High"
    elif confidence_score > 0.5:
        level = "Medium"
    else:
        level = "Low"

    confidence = ConfidenceInfo(score=confidence_score, level=level)

    return llm_output, sources, confidence
