# Production-style hybrid embedding workflow

## Mục tiêu

Thay vì lưu vector ngẫu nhiên thủ công trong file JSON, demo này sử dụng pipeline thực tế:

1. Lưu dữ liệu gốc dưới dạng documents JSON.
2. Sinh dense embedding bằng BGE-small-en-v1.5.
3. Sinh sparse embedding bằng BM25.
4. Tạo file points để upsert vào Qdrant.

## Cấu trúc

- documents_batch_01.json
- documents_batch_02.json
- generate_vectors.py
- points_batch_01.json
- points_batch_02.json

## Chạy

```powershell
cd D:\Qdrant\demo-local
D:\Qdrant\.venv\Scripts\python.exe .\sample_data\generate_vectors.py
```

## Kết quả

Mỗi point sẽ có:
- vector.dense: dense embedding 384 chiều
- vector.keywords.indices/values: sparse embedding
- payload: metadata và text gốc

## Nếu thấy ký tự lỗi (CÃ¡c, Ã…)

Nguyên nhân thường là do file JSON được đọc bằng encoding không đúng trước khi gửi lên Qdrant. Hãy đảm bảo:
- file được viết bằng UTF-8
- PowerShell đọc bằng UTF-8 khi gửi body
- nếu collection cũ đã nhận dữ liệu sai, xóa collection rồi upsert lại từ đầu
