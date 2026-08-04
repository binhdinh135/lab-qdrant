"""
Account Lookup Service: Tra cứu số tài khoản gần đúng.

Khi user nhập STK không đầy đủ → gợi ý danh sách khả dĩ
kèm điểm tin cậy và lý do khớp.
"""

import re
import json
from typing import List, Dict, Any
from pathlib import Path


# Load mock accounts
ACCOUNTS_PATH = Path(__file__).parent.parent / "data" / "accounts_mock.json"

MOCK_ACCOUNTS = [
    {"account": "1234567890", "name": "NGUYEN VAN A", "type": "CA (Thanh toán)"},
    {"account": "1234567001", "name": "TRAN THI B", "type": "SA (Tiết kiệm)"},
    {"account": "9876543210", "name": "CONG TY TNHH ABC", "type": "CA (Doanh nghiệp)"},
    {"account": "1234999888", "name": "LE VAN C", "type": "CA (Thanh toán)"},
]


def load_accounts() -> List[Dict]:
    """Load accounts từ file JSON nếu có, fallback sang mock."""
    if ACCOUNTS_PATH.exists():
        return json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
    return MOCK_ACCOUNTS


def search_account(query: str) -> List[Dict[str, Any]]:
    """
    Tra cứu STK gần đúng.
    
    Logic:
    - Trích xuất chữ số từ query
    - Tìm accounts có prefix khớp → score 0.96
    - Tìm accounts chứa chuỗi → score 0.80
    
    Returns: list kết quả sắp xếp theo score giảm dần.
    """
    accounts = load_accounts()
    digits = "".join(re.findall(r"\d+", query))

    if not digits:
        return []

    matches = []
    for acc in accounts:
        if acc["account"].startswith(digits):
            matches.append({
                "account": acc["account"],
                "name": acc["name"],
                "type": acc["type"],
                "score": 0.96,
                "reason": f"Khớp tiền tố STK '{digits}'"
            })
        elif digits in acc["account"]:
            matches.append({
                "account": acc["account"],
                "name": acc["name"],
                "type": acc["type"],
                "score": 0.80,
                "reason": f"Chứa chuỗi '{digits}'"
            })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
