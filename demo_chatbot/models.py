"""
Pydantic Models (Request/Response schemas) cho Smart Search Assistant.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class ChatRequest(BaseModel):
    """Request body cho /chat endpoint."""
    conversation_id: str = Field(..., example="session_001")
    question: str = Field(..., example="Quy trình mở CIF gồm những bước nào?")


class UploadDocRequest(BaseModel):
    """Request body cho /upload-doc endpoint."""
    filename: str = Field(..., example="QuyDinh_AnToan_Moi.md")
    content: str = Field(..., example="# Quy định An toàn\n\n## 1. Bảo mật...")


class SourceItem(BaseModel):
    """1 nguồn trích dẫn."""
    document: str
    section: Optional[str] = "N/A"
    content_snippet: str


class ConfidenceInfo(BaseModel):
    """Thông tin độ tin cậy."""
    score: float
    level: str  # "High", "Medium", "Low"


class UnifiedResponse(BaseModel):
    """
    Response thống nhất cho mọi loại câu hỏi.
    - type: "knowledge" | "operation" | "chitchat"
    - answer: câu trả lời (knowledge/chitchat)
    - sources: danh sách trích dẫn (knowledge)
    - results: kết quả tra cứu (operation)
    - confidence: điểm tin cậy
    """
    type: str
    answer: Optional[str] = None
    sources: Optional[List[SourceItem]] = None
    results: Optional[List[Dict[str, Any]]] = None
    confidence: ConfidenceInfo
