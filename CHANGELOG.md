# Changelog

All notable changes to this project will be documented in this file.

## [Phase 4] - 2026-11-21 (Contract v1.3, Release v1.0.0)
### Added
- **Contract v1.3:** khai `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`) ở gốc `game.contract.json`; `run_cmd` chạy `--mode day`. Gameplay, tuning, kho và JSONL giữ nguyên v1.2.
- **Benchmark có render** (`chonoi/bench.py`): Chrome/Edge headless 1280×720, làm nóng 3 s rồi đo, xuất `avg_fps, p1_low_fps, frames, measured_s, load_ms`.
- **Soak headless** (`chonoi/soak.py`): N Ngày trong một tiến trình bằng bot tất định; kế hoạch D1–D5 lặp ở Ngày 6–10; xuất `days, days_completed, crashes, results, duration_s`.
- **Live `--mode day`:** chơi trọn vòng ngày trên trình duyệt (sáng → quán → shop), nhận `pause`/`buy`/`shop_done`.
- UI: cảnh báo oxy/thủy quái/khách sắp giận, chế độ tương phản cao, phụ đề SFX.
### Fixed
- Dọn code trùng sau merge #13/#14 trong `sim/gather.py` (crash dòng lũ, vật phẩm nhân đôi, hao tươi gấp đôi).
- Snapshot pha shop không còn văng lỗi với kho cá thể; nâng cấp ở shop không còn ghi đè tuning dùng chung; thủy quái theo `from_day` hoạt động trong mode day.

## [Phase 3] - 2026-11-21 (Contract v1.2)
### Breaking Changes
- **Chuyển đổi Schema Kho:** Kho đếm theo loại (`{"items": {kind: count}}`) chính thức bị thay thế bởi **kho cá thể** (`{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`).
- Contract v1.2 trả mã thoát `2` khi nạp file kho đếm hoặc sai schema, kind lạ, id trùng, fresh ngoài `[0, 100]`.
- Bài kiểm thử hồi quy cũ `test_inv_01_gather_writes_inventory_quan_reads_it` được bỏ qua do định dạng kho đếm đã không còn hiệu lực ở v1.2.

### Added
- **Độ tươi (Freshness):**
  - Khai báo cấu hình `freshness` trong `game.contract.json`: `{initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.
  - Hao tươi giỏ: 0.5 điểm/s (kẹp đáy 0, đóng băng khi pause).
  - Hao tươi kho quán: 0.25 điểm/s (kẹp đáy 0, đóng băng khi pause).
  - Ngưỡng ươn: `< 30`, phát sự kiện `spoiled` với `{item_id, kind, location}`.
  - Giữ chỗ theo id cá thể tươi nhất; nếu cá thể đang giữ bị ươn thì nhả và thử giữ lại 1 lần.
  - Chốt giá món: `base_price = floor(giá niêm yết * avg_fresh / 100)`.
- **Mở rộng Dòng nước lũ (`current`):**
  - Khai báo extension `"current"` và cấu hình `gather.current`.
  - Chu kỳ dòng lũ mỗi 1800 tick, cảnh báo tại `t - 120`, kéo dài 480 tick với lực đẩy 1.5 m/s ở độ sâu `d >= 10`.
- **Hệ thống cấp ID cá thể:** Cấp ID dạng `I1, I2, ...` liên tục tăng xuyên pha và xuyên ngày qua `DaySim`.

## [Phase 2] - 2026-11-21 (Contract v1.1)
### Added
- Vòng lặp Ngày `DaySim` và cờ CLI `--days [1..5]`.
- Quán ăn mở rộng: 2 bếp (`B1, B2`), 4 bàn (`T1–T4`), thực đơn 6 món ăn, lọc món theo Kế hoạch ngày D1–D5.
- Cơ chế tạm dừng Pause/Resume đóng băng `sim_tick` và thời gian trò chơi.
- Thủy quái Cá Sấu (`ca_sau` M1, M2) và hệ thống cá bơi đổi hướng, sinh cá định kỳ 360 tick.

## [Phase 1] - 2026-11-21 (Contract v1.0)
### Added
- Khung mô phỏng Lặn (`sim/gather`) và Quán ăn (`sim/quan`).
- Hợp đồng kiểm thử cơ bản (Contract A-G).
- Bộ kiểm thử hộp đen smoke test `test_smoke_p1.py`.
