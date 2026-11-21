# Kế hoạch Phase 1 (≤ 1 trang)

## 1. Mục tiêu
- Hoàn thành toàn bộ logic cốt lõi cho cả 2 buổi: Lặn & Hái (`sim/gather`) và Mở quán (`sim/quan`).
- Đảm bảo chạy đúng hợp đồng headless (`test_smoke_p1.py` pass 100%, tất định byte-by-byte).
- Hoàn thành đầy đủ hồ sơ kiểm chứng, ma trận truy vết và gắn tag `phase-1` trước mốc 1:00.

## 2. Phân công việc / Người / Phụ thuộc

| Thành viên | Nhiệm vụ chính | Các lát việc cụ thể | Phụ thuộc |
|---|---|---|---|
| **Trần Đức Trung** (`sim/gather`) | Buổi sáng: Lặn & Hái | - **Lát 1:** Logic bơi, oxy, ngạt nước, mất máu, ngất xỉu, giỏ chứa.<br>- **Lát 2:** Hái bông điên điển/bông súng, bắt cá lóc/cá linh, kiểm tra giỏ đầy, cập bến bến đỗ (`docked`) và xuất file kho `inventory.json`. | Độc lập |
| **Đỗ Việt Anh** (`sim/quan`) | Buổi tối: Quán ăn | - **Lát 3:** Đón khách theo lịch, chọn món theo kho `stock`, giữ chỗ nguyên liệu (`reserved`), đếm ngược kiên nhẫn, khách bỏ về (`customer_left`), hết món (`no_dish`).<br>- **Lát 4:** Tương tác bếp (bắt đầu nấu, chín, nhấc món), phục vụ tại bàn, tính tiền, tip (khi phục vụ nhanh), uy tín và kết thúc ca (`quan_end`). | Nhận file kho từ `sim/gather` |
| **Nguyễn Phi Hoàng** (`chonoi/web`) | Giao diện Web / Canvas | - Cải thiện giao diện chơi trực tiếp trên trình duyệt (`chonoi/web/index.html`).<br>- Thêm HUD trực quan cho oxy, máu, giỏ đồ ở gather; trạng thái bếp, bàn và tiền/uy tín ở quán. | Đọc snapshot từ sim |
| **Nguyễn Công Hoàn** (`qa`) | Kiểm thử & Bằng chứng | - Viết thêm unit tests trong `tests/` kiểm tra các trường hợp biên của gather và quan.<br>- Chạy headless, kiểm tra tính tất định byte-by-byte.<br>- Điền ma trận truy vết `docs/verification/phase-1.md` và lưu log vào `docs/proof/phase-1/`. | Phụ thuộc code của Trung & Việt Anh |
| **Vũ Thành** (`integration`) | Quản lý tích hợp & Release | - Setup cấu hình repo, `TEAM.md`, `game.contract.json`.<br>- Viết ≥ 2 AI skills tại `.agents/skills/`, cập nhật `AGENTS.md` và `docs/ai-usage-log.md`.<br>- Điều phối merge nhánh, kiểm tra `tools/check_team.py`, gắn Git tag `phase-1`. | Toàn bộ nhóm |

## 3. Rủi ro & Giải pháp
- **Rủi ro 1: Xung đột khi gộp Git nhánh chính.**
  - *Giải pháp:* Chia file rõ ràng (`gather.py`, `quan.py`, `web/index.html`, `tests/`), mỗi người làm nhánh riêng, rebase trước khi merge.
- **Rủi ro 2: Không khớp hợp đồng kho giữa gather và quan.**
  - *Giải pháp:* Tuân thủ tuyệt đối schema `docs/contracts/inventory.sample.json`.
- **Rủi ro 3: Lỗi không tất định (Non-deterministic) khi chạy headless.**
  - *Giải pháp:* Chỉ dùng bộ tạo số ngẫu nhiên `self.rng` (`Streams`), tuyệt đối không dùng thư viện `random` toàn cục hoặc đồng hồ hệ thống.
