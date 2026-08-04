"""
Intent Classifier: Phân loại câu hỏi thành 3 loại.

- "chitchat"   : Chào hỏi, xã giao
- "operation"  : Tra cứu STK (có số >= 5 chữ số)
- "knowledge"  : Hỏi quy trình/quy chế nội bộ (RAG)
"""

import re


GREETING_KEYWORDS = [
    "chào", "hi", "hello", "bạn là ai", "giúp gì", "trợ lý",
    "xin chào", "hey", "bắt đầu"
]


def classify_intent(query: str) -> str:
    """
    Phân loại intent dựa trên rule-based.
    
    Logic:
    1. Nếu câu ngắn + chứa từ chào hỏi → chitchat
    2. Nếu có >= 5 chữ số liên tục hoặc keyword STK → operation
    3. Còn lại → knowledge (RAG)
    """
    q_lower = query.lower().strip()

    # Chitchat detection
    if len(q_lower) < 40:
        if any(kw in q_lower for kw in GREETING_KEYWORDS):
            return "chitchat"

    # Operation detection (account lookup)
    digits = re.findall(r"\d+", query)
    if digits and len(digits[0]) >= 5:
        return "operation"
    if any(kw in q_lower for kw in ["stk", "tài khoản", "số tài khoản"]):
        if digits:
            return "operation"

    # Default: knowledge QA
    return "knowledge"
