# Kế hoạch Phase 4 — Hoàn Thiện & Bàn Giao (Release v1.0.0)

## 1. Mục tiêu
- Nâng cấp Contract lên **v1.3**, hoàn thiện phiên bản phát hành chính thức **Release v1.0.0**.
- Cài đặt hai công cụ tiêu chuẩn theo Test Contract v1.3:
  - **Benchmark (`bench_cmd`):** `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` chạy kịch bản chuẩn có render trong trình duyệt (Chrome/Edge headless 1280×720), đo FPS trung bình (yêu cầu $\ge 60$ FPS), 1% low FPS (yêu cầu $\ge 30$ FPS), thời gian tải trang (yêu cầu $\le 10$ s) và xuất đủ 5 trường số liệu.
  - **Soak testing (`soak_cmd`):** `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` chạy mô phỏng dài ngày xuyên suốt 10 Ngày không lỗi/crash (`days_completed = 10`, `crashes = 0`), đảm bảo độ bền bộ nhớ và tính tất định byte-by-byte.
- Nâng cao khả năng tiếp cận (Accessibility) và mở rộng cho nhóm 5 người:
  - 3 cảnh báo trực quan bằng chữ/biểu tượng (thủy quái gần, cạn oxy, khách sắp giận) kết hợp chế độ tương phản cao (High Contrast mode) lưu trong `localStorage`.
  - Phụ đề SFX (hiển thị hành động và hiệu ứng âm thanh dưới dạng văn bản khi tắt tiếng).
- Hoàn thiện chế độ chơi trực tiếp xuyên ngày trên trình duyệt (`python3 -m chonoi.live --mode day`).
- Đảm bảo clone sạch chạy được trong $\le 3$ lệnh, regression toàn bộ 143/143 tests P1–P4 pass 100%, bảo toàn tính tất định SHA-256.
- Đóng gói toàn bộ hồ sơ nghiệm thu, gắn Git tag `phase-4` và tạo GitHub Release `v1.0.0`.

## 2. Bảng phân công nhiệm vụ & Tác động module

| Thành viên | Trách nhiệm | File phụ trách | Nhiệm vụ chi tiết |
|---|---|---|---|
| **Vũ Thành** (`integration`) | Integrator / Release Lead | `game.contract.json`, `chonoi/bench.py`, `chonoi/soak.py`, `chonoi/live.py`, `docs/plan/phase-4.md`, `CHANGELOG.md`, `README.md` | - Nâng Contract lên v1.3: khai báo `bench_cmd`, `soak_cmd`, `run_cmd` tại gốc `game.contract.json`.<br>- Cài đặt `chonoi/bench.py`: tự động phát hiện trình duyệt headless, mở server live với cờ benchmark, nhận delta rAF và kết xuất `bench.json`.<br>- Cài đặt `chonoi/soak.py`: vòng lặp 10 ngày tự động (bot shop), giám sát crash và ghi nhận `soak.json`.<br>- Bổ sung `--mode day` và đa ngày `--days` vào máy chủ live socket `chonoi/live.py`.<br>- Cập nhật hồ sơ bàn giao, hướng dẫn bắt đầu nhanh và chuẩn bị release. |
| **Trần Đức Trung** (`gather`) | Lát 1: Tối ưu hiệu năng Lặn & Hái | `chonoi/sim/gather.py` | - Rà soát giải phóng tài nguyên và tối ưu vòng lặp tick mô phỏng lặn để đáp ứng tần số quét cao khi benchmark.<br>- Đảm bảo các mảng thực thể cá thể (giỏ, đàn cá, quái vật) chạy ổn định qua nhiều ngày liên tiếp trong soak test. |
| **Đỗ Việt Anh** (`quan`) | Lát 2: Ổn định quán ăn xuyên ngày | `chonoi/sim/quan.py` | - Rà soát dọn dẹp các đơn đặt, khách rời đi và rác bộ nhớ giữa các ngày phục vụ.<br>- Đảm bảo tính liên tục của kho hàng cá thể khi chuyển giao giữa các ngày trong `DaySim` không gây leak bộ nhớ hay crash. |
| **Nguyễn Phi Hoàng** (`web`) | Client & Trợ năng (Accessibility) | `chonoi/web/index.html`, `chonoi/web/` | - Cài đặt chế độ tương phản cao (High Contrast toggle) với bảng màu độ tương phản cao (viền đen/vàng sáng).<br>- Hiển thị 3 cảnh báo trực quan: Thủy quái gần (viền tím), Oxy sắp cạn (nhấp nháy đỏ), Khách sắp giận (thanh kiên nhẫn chuyển đỏ cam).<br>- Cài đặt tính năng Phụ đề SFX khi tắt tiếng (âm thanh cạn oxy, tiếng cá cắn, tiếng chuông khách).<br>- Tích hợp hook rAF đo đạc thời gian khung hình cho chế độ `/bench`. |
| **Nguyễn Công Hoàn** (`qa`) | QA & Kiểm thử bàn giao | `tests/test_phase4.py`, `tests/test_live_day.py`, `docs/verification/phase-4.md`, `docs/proof/phase-4/` | - Xây dựng bộ test Phase 4 `test_phase4.py` (kiểm tra schema `bench.json`, `soak.json`, Contract v1.3).<br>- Xây dựng kiểm thử tích hợp máy chủ live `test_live_day.py` chạy qua socket loop.<br>- Thu thập bằng chứng thực tế cho ma trận truy vết `docs/verification/phase-4.md`.<br>- Chạy skill `verify-phase --phase 4` xuất log `smoke_test.txt` đạt 143/143 tests. |

## 3. Rủi ro kỹ thuật & Giải pháp kiểm soát

1. **Rủi ro môi trường không có Chrome/Edge khi chạy `bench_cmd`:**
   - *Giải pháp:* `chonoi/bench.py` hỗ trợ biến môi trường `CHONOI_BROWSER`, đồng thời có chế độ fallback đo tốc độ mô phỏng headless nếu không tìm thấy browser nhị phân, in cảnh báo rõ ràng trên stderr thay vì crash.
2. **Rủi ro sai lệch tính tất định trong `soak_cmd` xuyên suốt 10 ngày:**
   - *Giải pháp:* Khởi tạo một `Streams` duy nhất gắn liền với seed đầu vào (`seed=7`), không khởi tạo lại hạt giống giữa các ngày, giữ nguyên thứ tự tiêu thụ số ngẫu nhiên của các pha.
3. **Rủi ro xung đột lưu trữ cục bộ khi bật tính năng Accessibility:**
   - *Giải pháp:* Lưu tùy chọn chế độ tương phản cao vào `localStorage` có bọc khối `try...catch` phòng thủ (tránh lỗi trên các môi trường sandbox chặn truy cập storage).
