"""
Pydantic Models (DTO) cho project.

Tương đương Java:
  public class Document { String title; String department; ... }
  public class SearchRequest { String query; int limit; }

Pydantic giúp:
  - Validation tự động (kiểu dữ liệu, required/optional)
  - Serialize/Deserialize JSON
  - Dùng làm Request/Response model trong FastAPI
"""

from pydantic import BaseModel, Field
from typing import Optional


class Document(BaseModel):
    """Đại diện 1 document trong hệ thống."""
    document_id: str = Field(..., description="Mã tài liệu, vd: DOC-001")
    title: str = Field(..., description="Tiêu đề tài liệu")
    text: str = Field(..., description="Nội dung text")
    department: str = Field(..., description="Phòng ban: NHAN_SU, CNTT, KE_TOAN")
    domain: str = Field(default="general", description="Lĩnh vực: nhan_su, cong_nghe, hanh_chinh")
    doc_type: str = Field(default="general", description="Loại: quy_dinh, huong_dan, chinh_sach")
    doc_status: str = Field(default="ACTIVE", description="Trạng thái: ACTIVE, ARCHIVED")


class SearchRequest(BaseModel):
    """Request body cho endpoint /search."""
    query: str = Field(..., min_length=1, description="Câu hỏi tìm kiếm")
    limit: int = Field(default=5, ge=1, le=20, description="Số kết quả trả về")
    department: Optional[str] = Field(default=None, description="Filter theo phòng ban")


class SearchResult(BaseModel):
    """1 kết quả search."""
    id: int
    score: float
    title: str
    text: str
    department: str


class UpsertRequest(BaseModel):
    """Request body cho endpoint /upsert."""
    document_id: str
    title: str
    text: str
    department: str
    domain: str = "general"
    doc_type: str = "general"
