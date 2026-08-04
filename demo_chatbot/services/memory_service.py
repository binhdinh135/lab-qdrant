"""
Conversation Memory Service: Lưu lịch sử hội thoại theo session.

Giúp trợ lý hiểu câu hỏi nối tiếp (vd: "bước tiếp theo là gì?")
mà không cần hỏi lại từ đầu.
"""

from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


# In-memory session store (production nên dùng Redis)
SESSION_STORE: Dict[str, List[BaseMessage]] = {}

# Giới hạn lịch sử (tránh prompt quá dài)
MAX_HISTORY_MESSAGES = 10


def get_history(conversation_id: str) -> List[BaseMessage]:
    """Lấy lịch sử hội thoại của session."""
    return SESSION_STORE.get(conversation_id, [])


def add_message(conversation_id: str, role: str, content: str):
    """Thêm message vào lịch sử."""
    if conversation_id not in SESSION_STORE:
        SESSION_STORE[conversation_id] = []

    if role == "user":
        SESSION_STORE[conversation_id].append(HumanMessage(content=content))
    else:
        SESSION_STORE[conversation_id].append(AIMessage(content=content))

    # Trim nếu quá dài
    if len(SESSION_STORE[conversation_id]) > MAX_HISTORY_MESSAGES:
        SESSION_STORE[conversation_id] = SESSION_STORE[conversation_id][-MAX_HISTORY_MESSAGES:]


def clear_session(conversation_id: str):
    """Xóa lịch sử session."""
    SESSION_STORE.pop(conversation_id, None)
