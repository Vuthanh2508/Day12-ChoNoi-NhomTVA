# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt:
  - Phân chia module rành mạch theo lát cắt dọc (`sim/gather` làm cá sấu & đàn cá, `sim/quan` làm 2 bếp 4 bàn và thực đơn 6 món), các thành viên phát triển song song không đè code nhau.
  - Vòng lặp ngày `DaySim` và cơ chế Pause đóng băng thời gian hoạt động mượt mà, giữ đúng tính tất định (SHA-256 trùng khớp 100%).
  - Tiến độ bàn giao đúng hạn, bộ test nâng lên 93/93 tests đều xanh.
- Điều tệ:
  - Chưa tạo kịp file tài liệu kế hoạch `docs/plan/phase-2.md` ngay từ đầu phase (đến Phase 3 mới phát hiện và phải bổ sung lại).
  - Khi ghép logic cá sấu cắn rơi đồ và kho quán nhiều ngày, ban đầu có nguy cơ lệch ID thực thể nếu khởi tạo lại bộ cấp phát ID giữa các ngày.
- 1 hành động cho Phase 3:
  - Integrator sẽ chủ động ban hành trước adapter hợp đồng kho cá thể (Contract v1.2) và test chấp nhận lên nhánh `main` trước khi cả nhóm phân nhánh code chi tiết, tránh xung đột cấu trúc dữ liệu kho.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
  - **Đã làm và làm rất tốt:** Ngay đầu Phase 3, Integrator (Vũ Thành) đã cấu hình xong Contract v1.2 trong `game.contract.json`, bổ sung adapter kho cá thể trong `inventory.py`, `sim/day.py` và viết test `test_inventory_phase3.py` trên nhánh `main`. Nhờ đó, các bạn làm lát `gather` và `quan` khi pull về đều bám sát đúng một schema chung, việc tích hợp diễn ra trơn tru.
- Điều tốt / điều tệ:
  - **Điều tốt:**
    - Hiệu năng hệ thống rất cao: Benchmark có render đạt 119.87 FPS trung bình và 79.96 FPS 1% low (vượt xa chuẩn $\ge 60$ FPS và $\ge 30$ FPS); thời gian tải trang chỉ 789 ms ($\le 10$ s).
    - Soak test 10 ngày chạy trơn tru, hoàn thành 10/10 ngày với 0 crash, chứng minh hệ thống không bị rò rỉ bộ nhớ hay lỗi tích lũy dữ liệu qua nhiều ngày.
    - Bộ test tự động bao phủ toàn diện 143/143 tests (tăng từ 57 ở P1 $\rightarrow$ 93 ở P2 $\rightarrow$ 135 ở P3 $\rightarrow$ 143 ở P4). Hai công cụ AI skill (`verify-phase`, `inventory-validator`) giúp tự động hóa khâu nghiệm thu và trích xuất bằng chứng nhanh chóng, chính xác.
    - Tính năng Accessibility (tương phản cao, 3 cảnh báo trực quan) và mở rộng cho nhóm 5 người (phụ đề SFX, dòng nước lũ) chạy ổn định và giữ vững tính tất định byte-by-byte.
  - **Điều tệ:**
    - Khi merge PR #13 và PR #14 ở Phase 3 xuất hiện xung đột kiểu dữ liệu giữa biến `current_direction` (int vs None) gây fail một test biên ở `gather.py:677`, nhóm phải mất thêm 1 PR hotfix #15 để xử lý triệt để.
    - Bạn Hoàng gặp trục trặc đường truyền mạng cục bộ nên một số commit phải thực hiện dưới hình thức ghép cặp (pair programming) cùng Integrator, dẫn đến số commit độc lập ghi nhận trên tài khoản cá nhân ít hơn các bạn khác.
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
  - **Số commit theo người (tổng hợp qua các nhánh và merge PR):**
    - Vũ Thành (`Vuthanh2508`): 26 commits (Khởi tạo repo, Contract v1.0–v1.3, tích hợp, AI skills, bench, soak, live day, hồ sơ release)
    - Nguyễn Công Hoàn (`hoan11052004`): 10 commits (QA test suites, kiểm thử chấp nhận P1–P4, UI accessibility)
    - Trần Đức Trung (`kientrungtd135` / `Tran Duc Trung`): 7 commits (Lát Gather: cơ chế bơi, đàn cá, cá sấu, dòng lũ, giỏ cá thể)
    - Đỗ Việt Anh (`vietahnn` / `vietanh`): 10 commits (Lát Quán: 2 bếp 4 bàn, thực đơn 6 món, hao tươi kho, phục vụ, giá & tip)
    - Nguyễn Phi Hoàng (`phihoang1709`): 2 commits độc lập + các commit co-authored pair programming (Giao diện Web Canvas, HUD, theme Tây Nam Bộ)
  - **Cách đọc code của nhau:**
    - Review chéo PR theo cặp module liền kề: `sim/gather` đọc `sim/quan`, QA đọc cả hai module; Integrator rà soát tổng thể hợp đồng và chạy regression test trước khi merge vào nhánh `main`.
  - **Ước tính token AI sử dụng:**
    - Trung bình mỗi thành viên tiêu thụ khoảng 200k – 350k tokens thông qua các công cụ hỗ trợ như Antigravity / Gemini CLI / Claude trong toàn bộ quá trình phát triển 4 phase.
- Một lần AI sai và cách nhóm phát hiện:
  - Trong Phase 3 khi lập trình cơ chế hao độ tươi ở `gather.py`, AI đã đề xuất trừ độ tươi của giỏ đồ trong mọi tick mà không kiểm tra trạng thái tạm dừng, khiến cho khi bấm `pause`, thực phẩm vẫn tiếp tục bị giảm độ tươi.
  - **Cách nhóm phát hiện:** QA chạy bộ kiểm thử `test_gather_phase3_final.py` (`test_pause_stops_freshness_and_simulation`), test bị FAIL do khi pause thì độ tươi của vật phẩm vẫn giảm. Nhóm đã tra soát mã nguồn, phát hiện AI bỏ sót điều kiện `if self.paused: return` trước đoạn xử lý hao tươi, nhóm đã sửa lại điều kiện này và test lập tức vượt qua.
- Nếu làm lại, đổi gì:
  - Cấu hình đồng bộ `git config user.name` và `user.email` của toàn bộ thành viên ngay từ 15 phút kickoff để tên tác giả commit khớp 100% với GitHub handle trong `TEAM.md`, tránh việc một người có nhiều tên tác giả khác nhau trên git log.
  - Soạn sẵn toàn bộ khung thư mục `docs/plan/` cho cả 4 phase ngay từ đầu để tránh việc thiếu sót kế hoạch như ở Phase 2.
  - Định nghĩa rõ các kiểu dữ liệu và giá trị mặc định (như `0` thay vì `None`) trong hợp đồng để tránh xung đột type khi các nhánh song song merge vào nhau.
