---
name: inventory-validator
description: Kiểm định file kho nguyên liệu theo chuẩn Contract G v1.3 (kho cá thể {id, kind, fresh}, tươi >= 30) và phân tích khả năng nấu các món trong menu 6 món.
---

# Skill: inventory-validator (Kiểm định File Kho Contract G v1.3)

## Khi nào dùng
- Sử dụng sau khi chạy buổi sáng (`gather`) để kiểm tra file kho xuất ra có hợp lệ theo chuẩn cá thể Contract v1.3 trước khi đưa vào buổi tối (`quan`).
- Sử dụng để phát hiện sớm các lỗi sai schema (nguyên liệu lạ, id trùng, độ tươi ngoài miền [0, 100], định dạng kho đếm cũ v1.0 bị cấm) trước khi chạy test.

## Lệnh thực thi
```bash
python .agents/skills/inventory-validator/validate_inventory.py docs/contracts/inventory.v12.sample.json
```

## Kết quả đầu ra
1. Kiểm tra cấu trúc `{"items": [{"id": "...", "kind": "...", "fresh": ...}]}` chuẩn Contract G v1.3.
2. Kiểm tra tính hợp lệ của ID cá thể duy nhất, tên nguyên liệu trong 6 loại cho phép, và miền giá trị độ tươi `[0, 100]`.
3. Lọc các nguyên liệu khả dụng có độ tươi $\ge 30$ (loại trừ các cá thể bị ươn `< 30`).
4. Phân tích số suất món ăn tối đa quán có thể phục vụ được theo Menu 6 món chuẩn Tây Nam Bộ.
