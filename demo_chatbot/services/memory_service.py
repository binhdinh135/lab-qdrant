"""
Conversation Memory Service - Chuẩn LangChain.

Dùng ChatMessageHistory + FileChatMessageHistory để:
- Tự quản lý lịch sử theo session_id
- Persist ra file (tắt bật vẫn giữ)
- Tích hợp trực tiếp với MessagesPlaceholder trong prompt

LangChain flow:
  conversation_id → get_history(session_id) → ChatMessageHistory
  → messages tự inject vào MessagesPlaceholder trong prompt chain
"""

from typing import Dict
from pathlib import Path

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_community.chat_message_histories import FileChatMessageHistory


# Folder lưu sessions (persist qua file)
SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Store: session_id → ChatMessageHistory instance
_store: Dict[str, BaseChatMessageHistory] = {}


def get_history(session_id: str) -> BaseChatMessageHistory:
    """
    Lấy ChatMessageHistory theo session_id.
    
    - Lần đầu: tạo FileChatMessageHistory (load từ file nếu có)
    - Lần sau: trả từ cache
    
    Dùng trực tiếp với RunnableWithMessageHistory hoặc đọc .messages
    """
    if session_id not in _store:
        # FileChatMessageHistory persist ra file JSON tự động
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        file_path = str(SESSIONS_DIR / f"{safe_id}.json")
        _store[session_id] = FileChatMessageHistory(file_path=file_path)
    return _store[session_id]


def add_user_message(session_id: str, content: str):
    """Thêm tin nhắn user vào history."""
    history = get_history(session_id)
    history.add_user_message(content)


def add_ai_message(session_id: str, content: str):
    """Thêm tin nhắn AI vào history."""
    history = get_history(session_id)
    history.add_ai_message(content)


def get_messages(session_id: str):
    """Lấy list messages (dùng cho MessagesPlaceholder)."""
    history = get_history(session_id)
    return history.messages


def clear_session(session_id: str):
    """Xóa lịch sử session."""
    history = get_history(session_id)
    history.clear()
    _store.pop(session_id, None)
