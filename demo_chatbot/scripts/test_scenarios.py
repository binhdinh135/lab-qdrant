r"""
Script chạy tự động 4 kịch bản nghiệm thu.

Gọi API /chat và kiểm tra response format.

Chạy:
  cd /d D:\Qdrant\demo_chatbot
  D:\Qdrant\.venv\Scripts\python.exe scripts\test_scenarios.py
"""

import json
import sys
from urllib import request, error

API_URL = "http://localhost:8000"
SESSION_ID = "test_auto_001"


def call_chat(question: str) -> dict:
    """Gọi POST /chat."""
    body = json.dumps({
        "conversation_id": SESSION_ID,
        "question": question,
    }).encode("utf-8")

    req = request.Request(
        f"{API_URL}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def print_result(scenario: str, question: str, result: dict):
    """In kết quả đẹp."""
    print(f"\n{'─' * 60}")
    print(f"📋 {scenario}")
    print(f"   Q: {question}")
    print(f"   Type: {result['type']}")
    print(f"   Confidence: {result['confidence']['score']} ({result['confidence']['level']})")

    if result.get("answer"):
        print(f"   A: {result['answer'][:120]}...")

    if result.get("sources"):
        for src in result["sources"]:
            print(f"   📄 Source: {src['document']} (Mục {src['section']})")

    if result.get("results"):
        for r in result["results"]:
            print(f"   🔍 {r['account']} - {r['name']} (score={r['score']}, {r['reason']})")


def main():
    print("=" * 60)
    print("TEST 4 KỊCH BẢN NGHIỆM THU - SMART SEARCH ASSISTANT")
    print("=" * 60)
    print(f"API: {API_URL}")
    print(f"Session: {SESSION_ID}")

    try:
        # Kịch bản 0: Chitchat
        r = call_chat("Xin chào, bạn giúp gì được cho tôi?")
        print_result("KB0: Chào hỏi (chitchat)", "Xin chào, bạn giúp gì được cho tôi?", r)
        assert r["type"] == "chitchat", f"Expected chitchat, got {r['type']}"

        # Kịch bản 1: Trả lời có trích dẫn
        r = call_chat("Quy trình mở CIF gồm những bước nào?")
        print_result("KB1: Trả lời có trích dẫn", "Quy trình mở CIF gồm những bước nào?", r)
        assert r["type"] == "knowledge", f"Expected knowledge, got {r['type']}"
        assert r.get("sources"), "Expected sources in response"

        # Kịch bản 2: Tra cứu STK gần đúng
        r = call_chat("1234567")
        print_result("KB2: Tra cứu STK gần đúng", "1234567", r)
        assert r["type"] == "operation", f"Expected operation, got {r['type']}"
        assert r.get("results"), "Expected results in response"

        # Kịch bản 3: Hỏi nối tiếp (conversation memory)
        r = call_chat("Thời gian xử lý mất bao lâu?")
        print_result("KB3: Hỏi nối tiếp (memory)", "Thời gian xử lý mất bao lâu?", r)
        assert r["type"] == "knowledge", f"Expected knowledge, got {r['type']}"

        print(f"\n{'=' * 60}")
        print("✅ TẤT CẢ 4 KỊCH BẢN PASSED!")
        print("=" * 60)

    except error.URLError as e:
        print(f"\n❌ Không kết nối được API: {e}")
        print(f"   Hãy chạy trước: python -m uvicorn app:app --port 8000")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
