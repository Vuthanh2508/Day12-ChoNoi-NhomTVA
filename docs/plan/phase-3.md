# Kế hoạch Phase 3 — Mùa Nước Nổi (Change Request TICKET-03)

## 1. Mục tiêu
- Cập nhật Contract lên **v1.2**, chuyển đổi hoàn toàn cơ chế kho từ **kho đếm theo loại** sang **kho cá thể** `{"items": [{"id": "I1", "kind": "...", "fresh": 100}, ...]}`.
- Cài đặt cơ chế hao tươi (giỏ: 0.5/s, kho quán: 0.25/s), sự kiện ươn `spoiled` khi fresh < 30, giữ chỗ theo id cá thể tươi nhất và thử giữ lại khi bị ươn, chốt giá món theo độ tươi trung bình.
- Hoàn thành mở rộng bắt buộc cho nhóm 5 người: **Dòng nước lũ (`current`)** trong gather.
- Bàn giao kho nguyên tử (file và mode day), kiểm chứng tất định SHA-256, gắn tag `phase-3` trước mốc 2:30.

## 2. Bảng phân công nhiệm vụ & Tác động module

| Thành viên | Trách nhiệm | File cần sửa | Test liên quan | Đầu ra kỳ vọng |
|---|---|---|---|---|
| **Vũ Thành** (`integration`) | Integrator / Release Lead | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/day.py`, `docs/plan/phase-3.md`, `CHANGELOG.md` | `test_inventory_phase3.py`, `test_smoke_p1.py`, `verify-phase` | Contract v1.2, schema kho cá thể, từ chối kho đếm mã 2, cấp id I1..In xuyên ngày |
| **Trần Đức Trung** (`sim/gather`) | Lát 1: Lặn & Dòng lũ | `chonoi/sim/gather.py` | `test_gather_phase3_freshness.py`, `test_gather_phase3_current.py` | Giỏ cá thể, hao tươi 0.5/s, event spoiled, LIFO khi ngất/hit, Dòng lũ current 1800k |
| **Đỗ Việt Anh** (`sim/quan`) | Lát 2: Quán & Độ tươi | `chonoi/sim/quan.py` | `test_quan_phase3_freshness.py`, `test_quan_phase3_pricing.py` | Kho cá thể, hao 0.25/s, giữ theo id tươi nhất, thử giữ lại khi ươn, chốt base_price theo fresh |
| **Nguyễn Phi Hoàng** (`chonoi/web`) | HUD / Frontend | `chonoi/web/index.html`, `chonoi/web/` | Chơi trực tiếp trên trình duyệt | Hiển thị độ tươi, cảnh báo hàng ươn < 30, cảnh báo dòng lũ |
| **Nguyễn Công Hoàn** (`qa`) | QA & Kiểm thử biên | `tests/test_phase3_qa.py`, `docs/verification/phase-3.md` | Chạy bộ test v1.2, xuất log `docs/proof/phase-3/smoke_test.txt` | 100% test pass, kiểm tra tính tất định SHA-256 |

## 3. Quyết định kỹ thuật & Quy trình tích hợp
1. **Thứ tự tích hợp:**
   - Bước 1 (Đã xong): Integrator nâng `game.contract.json` lên v1.2, cập nhật adapter kho `chonoi/inventory.py` và `chonoi/sim/day.py` trên nhánh `main`.
   - Bước 2: Devs (Trung, Việt Anh, Hoàng, Hoàn) pull `main` về branch tính năng và phát triển song song.
   - Bước 3: Merge PRs của các thành viên vào `main`.
   - Bước 4: Chạy regression toàn bộ bộ test, xác nhận tính tất định và gắn tag `phase-3`.
2. **Quản lý ID cá thể:**
   - Cấp ID dạng `I1, I2, ...` liên tục tăng qua các ngày bằng `self.ids.new("I")`.
   - Các ID vật lý là duy nhất giữa các nơi chứa (giỏ, kho, đơn đặt).
3. **Độ tươi & Tính toán giá:**
   - Dùng phép so sánh ngưỡng trước khi làm tròn.
   - Chốt giá món: `base_price = floor(giá niêm yết * trung bình fresh của các cá thể nấu / 100)`.
   - Tiền boa: `floor(base_price * 0.2)`.
