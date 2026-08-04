"""
Script tạo JWT Token cho Kịch bản 2: Phân quyền theo Collection.

Cách dùng:
    1. Lấy secret key từ Qdrant:
       curl.exe -X GET "http://localhost:6380/cluster/secret-key" -H "api-key: admin-secret-key-2024"
    2. Paste secret key khi script hỏi.
    3. Script sẽ tạo 2 file: token_hr.txt và token_it.txt

Yêu cầu: pip install pyjwt
"""

import jwt
import datetime
import os

def main():
    # Lấy secret key
    secret = input("Nhập JWT secret key (lấy từ /cluster/secret-key): ").strip()
    
    if not secret:
        print("ERROR: Secret key không được để trống!")
        return

    # Token cho team HR - chỉ truy cập collection hr_docs
    token_hr_payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "access": [
            {
                "collection": "hr_docs",
                "access": "rw"  # read + write
            }
        ]
    }

    # Token cho team IT - chỉ truy cập collection it_docs
    token_it_payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "access": [
            {
                "collection": "it_docs",
                "access": "rw"  # read + write
            }
        ]
    }

    token_hr = jwt.encode(token_hr_payload, secret, algorithm="HS256")
    token_it = jwt.encode(token_it_payload, secret, algorithm="HS256")

    # Lưu file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(script_dir, "token_hr.txt"), "w") as f:
        f.write(token_hr)
    
    with open(os.path.join(script_dir, "token_it.txt"), "w") as f:
        f.write(token_it)

    print(f"\n✅ Đã tạo token thành công!")
    print(f"   - token_hr.txt (quyền: hr_docs, rw)")
    print(f"   - token_it.txt (quyền: it_docs, rw)")
    print(f"\n📋 Token HR: {token_hr[:50]}...")
    print(f"📋 Token IT: {token_it[:50]}...")


if __name__ == "__main__":
    main()
