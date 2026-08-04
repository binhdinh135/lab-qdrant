"""
Intent Classifier dùng LLM (LangChain + Ollama).

LLM sẽ phân loại câu hỏi thành 1 trong 3 loại:
- "chitchat"   : Chào hỏi, xã giao
- "operation"  : Tra cứu STK (số tài khoản)
- "knowledge"  : Hỏi quy trình/quy chế nội bộ (RAG)
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

_classifier_chain = None


def _get_classifier_chain():
    global _classifier_chain
    if _classifier_chain is None:
        from config import LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_BASE_URL

        if LLM_PROVIDER == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
        elif LLM_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI
            from config import OPENAI_API_KEY
            llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0)
        else:
            # Fake fallback
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Bạn là bộ phân loại intent. Phân loại câu hỏi người dùng thành ĐÚNG 1 trong 3 loại:

- chitchat: Chào hỏi, xã giao, hỏi bot là ai (vd: "xin chào", "bạn là ai")
- operation: Tra cứu số tài khoản, có chứa dãy số >= 5 chữ số (vd: "1234567", "STK 9876543210")
- knowledge: Hỏi về quy trình, quy định, hướng dẫn nội bộ (vd: "Quy trình mở CIF", "Mật khẩu tối thiểu bao nhiêu")

Chỉ trả lời ĐÚNG 1 từ: chitchat hoặc operation hoặc knowledge. Không giải thích."""),
            ("human", "{question}")
        ])

        _classifier_chain = prompt | llm | StrOutputParser()

    return _classifier_chain


def classify_intent(query: str) -> str:
    """
    Phân loại intent bằng LLM (LangChain chain).

    Flow: prompt → LLM → parse output → "chitchat" / "operation" / "knowledge"
    """
    chain = _get_classifier_chain()

    if chain is None:
        # Fallback nếu không có LLM
        return _fallback_classify(query)

    try:
        result = chain.invoke({"question": query})
        # Clean output
        intent = result.strip().lower().replace('"', '').replace("'", "")

        # Validate
        if intent in ("chitchat", "operation", "knowledge"):
            return intent

        # Nếu LLM trả lời không đúng format → fallback
        if "operation" in intent or "tài khoản" in intent:
            return "operation"
        if "chitchat" in intent or "chào" in intent:
            return "chitchat"
        return "knowledge"

    except Exception as e:
        print(f"[Intent Classifier] LLM error: {e}, using fallback")
        return _fallback_classify(query)


def _fallback_classify(query: str) -> str:
    """Rule-based fallback nếu LLM không available."""
    import re
    q_lower = query.lower().strip()

    digits = re.findall(r"\d+", query)
    if digits and len(digits[0]) >= 5:
        return "operation"

    greeting_kw = ["chào", "hello", "hi ", "bạn là ai", "giúp gì"]
    if len(q_lower) < 30 and any(kw in q_lower for kw in greeting_kw):
        return "chitchat"

    return "knowledge"
