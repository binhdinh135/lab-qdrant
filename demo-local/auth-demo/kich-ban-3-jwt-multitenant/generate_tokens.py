"""
Script tạo JWT Token cho Kịch bản 3: Multi-tenant (payload filter).

Mỗi token chứa claim "access" với "payload" filter.
Format payload trong JWT: {"key": "value"} (giá trị trực tiếp, KHÔNG dùng match syntax).
Khi user search, Qdrant tự thêm filter department vào query.

Cách dùng:
    cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
    D:\Qdrant\.venv\Scripts\python.exe generate_tokens.py
    Nhập secret key: admin-secret-key-2024

Yêu cầu: pip install pyjwt
"""

import jwt
import datetime
import os


def main():
    secret = input("Nhập JWT secret key: ").strip()

    if not secret:
        print("ERROR: Secret key không được để trống!")
        return

    # Token cho phòng Nhân sự - đọc + ghi, filter department=NHAN_SU
    token_nhansu_payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "access": [
            {
                "collection": "company_docs",
                "access": "rw",
                "payload": {
                    "department": "NHAN_SU"
                }
            }
        ]
    }

    # Token cho phòng CNTT - đọc + ghi, filter department=CNTT
    token_cntt_payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "access": [
            {
                "collection": "company_docs",
                "access": "rw",
                "payload": {
                    "department": "CNTT"
                }
            }
        ]
    }

    # Token cho phòng Kế toán - đọc + ghi, filter department=KE_TOAN
    token_ketoan_payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "access": [
            {
                "collection": "company_docs",
                "access": "rw",
                "payload": {
                    "department": "KE_TOAN"
                }
            }
        ]
    }

    token_nhansu = jwt.encode(token_nhansu_payload, secret, algorithm="HS256")
    token_cntt = jwt.encode(token_cntt_payload, secret, algorithm="HS256")
    token_ketoan = jwt.encode(token_ketoan_payload, secret, algorithm="HS256")

    # Lưu file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(script_dir, "token_nhansu.txt"), "w") as f:
        f.write(token_nhansu)

    with open(os.path.join(script_dir, "token_cntt.txt"), "w") as f:
        f.write(token_cntt)

    with open(os.path.join(script_dir, "token_ketoan.txt"), "w") as f:
        f.write(token_ketoan)

    print(f"\n✅ Đã tạo 3 token thành công!")
    print(f"   - token_nhansu.txt  (filter: department=NHAN_SU)")
    print(f"   - token_cntt.txt    (filter: department=CNTT)")
    print(f"   - token_ketoan.txt  (filter: department=KE_TOAN)")
    print(f"\n📋 Token Nhân sự: {token_nhansu[:50]}...")
    print(f"📋 Token CNTT:    {token_cntt[:50]}...")
    print(f"📋 Token Kế toán: {token_ketoan[:50]}...")


if __name__ == "__main__":
    main()
