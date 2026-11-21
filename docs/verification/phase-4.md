# Kiểm chứng Phase 4 · Contract v1.3 (Release v1.0.0)

Mã commit bàn giao tính năng Phase 4: `ee2749d` (PR #16), tích hợp hoàn tất trên `main`. Máy đo: Windows 11, Python 3.13, Microsoft Edge headless 1280×720.

## Ma trận truy vết

| AC | Yêu cầu | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 | `bench_cmd` chạy cảnh chuẩn và tạo `bench.json` đủ 5 trường | [bench.json](../proof/phase-4/bench.json): 3597 khung, 30.008 s, **avg 119.87 FPS, 1% low 79.96 FPS, load 789 ms**. Lệnh: `python -m chonoi.bench --seed 42 --duration 30 --out bench.json`. Test công thức: `tests/test_phase4.py` | Đạt, vượt cả 3 mốc báo cáo (≥60 FPS, ≥30 FPS, ≤10 s) |
| AC-P4-02 | `soak_cmd` chạy 10 Ngày, `days_completed = days`, `crashes = 0`, tất định | [soak.json](../proof/phase-4/soak.json): 10/10 ngày, 0 crash, 5.985 s. Hai lần chạy seed 7 giống nhau ở mọi trường trừ `duration_s`. Test: `SoakTests` | Đạt |
| AC-P4-03 | Contract v1.3 khai `bench_cmd`, `soak_cmd` ở gốc; gameplay/tuning/kho/JSONL theo v1.2 | `game.contract.json`; `ContractV13Tests`. Chỉ test `test_phase3_qa` đổi (kiểm version `1.2` → `1.3`), lý do ghi trong commit | Đạt |
| AC-P4-04 | Ba cảnh báo (thủy quái gần, oxy sắp hết, khách sắp giận) bằng chữ/biểu tượng và chế độ tương phản cao | Đã kiểm bằng Edge headless với dữ liệu mẫu (QA, trước PR này): sau khi bấm nút tương phản cao Canvas vẽ đủ cả ba cảnh báo; tùy chọn lưu trong trình duyệt. **Chưa chơi lại ba cảnh báo ở tương phản cao trong một lượt chơi thật** | Đạt với fixture; cần người chơi thử |
| AC-P4-05 | Phụ đề SFX khi tắt tiếng (mở rộng) | Edge headless: tắt tiếng rồi event `oxygen_empty` hiện phụ đề, không tạo bộ phát âm thanh (QA, trước PR này) | Đạt với fixture |
| AC-P4-06 | Clone sạch chạy bằng ≤ 3 lệnh | README mục "Bắt đầu nhanh": `git clone … && cd …` rồi `python3 -m chonoi.live --mode day`. Đã thử trên bản sao không có `.git` ở Windows: headless chạy được, live mở được cổng, 144/144 test | Đạt trên Windows. **Chưa thử trên macOS/Linux** |
| AC-P4-07 | Regression P1–P3 còn hiệu lực | [smoke_test.txt](../proof/phase-4/smoke_test.txt): 144/144 test, tính tất định byte-for-byte | Đạt |
| AC-P4-08 | Chơi trọn một Ngày (Lặn & Hái → Mở Quán → đóng Shop) | `tests/test_live_day.py` chơi 2 ngày qua máy chủ live: khách vào, shop, ngày kế, kết thúc `days_complete`. **Chưa có video/chơi tay trên trình duyệt** | Đạt ở mức test; cần chơi thử để demo |
| AC-P4-09 | Tag `phase-4` và Release `v1.0.0` cùng commit trên main | Đầy đủ điều kiện nghiệm thu, gắn tag `phase-4` và `v1.0.0` tại commit chốt trên main | Đạt |

## Giới hạn đã biết (ghi trung thực)
- Benchmark chạy trong Chrome/Edge headless, không đo GPU thật; FPS trần theo tần số làm tươi của máy đo (~120 Hz). Nếu không có trình duyệt, `bench_cmd` đo dự phòng chỉ phần mô phỏng (có cảnh báo trên stderr).
- Bot soak chỉ hành động ở Shop (mua nâng cấp, đóng shop); gather/quán để trống nên `earned` bằng 0. Soak kiểm độ bền xuyên ngày, không kiểm cân bằng kinh tế.
- Chưa làm bảng xếp hạng cục bộ (mở rộng tùy chọn).
- Đã bổ sung file `LICENSE` theo giấy phép mã nguồn mở của nhóm.
