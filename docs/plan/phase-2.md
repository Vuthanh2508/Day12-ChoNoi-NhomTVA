# Kế hoạch Phase 2 — Một Ngày Ở Chợ Nổi (Change Request TICKET-02)

## 1. Mục tiêu
- Nâng cấp Contract lên **v1.1**, hoàn thiện vòng lặp trọn vẹn một ngày (Day loop): **Sáng (Lặn & Hái) → Tối (Mở Quán) → Đêm (Chợ Chú Sáu / Nâng cấp)**.
- Hỗ trợ chạy đa ngày với cờ `--days <N>` và chế độ `--mode day`.
- Nâng cấp gameplay:
  - **Lặn & Hái (`gather`):** Hành vi đàn cá động (đổi hướng mỗi 120 tick, phản xạ mép, sinh mới mỗi 360 tick theo trọng số loài); xuất hiện chướng ngại vật/quái vật nguy hiểm (Cá Sấu tuần tra, phát hiện và rượt đuổi, cắn mất máu và rơi đồ LIFO).
  - **Mở Quán (`quan`):** Mở rộng không gian quán với 2 bếp nấu (`B1`, `B2`) và 4 bàn phục vụ (`T1`–`T4`); bổ sung thực đơn 6 món ăn Tây Nam Bộ; khách gọi món bám sát Kế hoạch ngày (`day_plan` từ D1 đến D5).
  - **Chợ Chú Sáu (`shop`):** Mua sắm nâng cấp bình Oxy tối đa và Máu tối đa (`hp_max`), có hiệu lực từ ngày kế tiếp.
  - **Cơ chế Pause:** Hỗ trợ phím tạm dừng đóng băng toàn bộ đồng hồ và trạng thái mô phỏng.
- Đảm bảo 100% test suites vượt qua, kiểm chứng tính tất định byte-by-byte (SHA-256) và gắn tag `phase-2` đúng hạn.

## 2. Bảng phân công nhiệm vụ & Tác động module

| Thành viên | Trách nhiệm | File phụ trách | Nhiệm vụ chi tiết |
|---|---|---|---|
| **Vũ Thành** (`integration`) | Integrator / Release Lead | `game.contract.json`, `chonoi/sim/day.py`, `chonoi/runner.py`, `chonoi/headless.py`, `docs/plan/phase-2.md`, `CHANGELOG.md` | - Cập nhật Contract v1.1: khai báo menu 6 món, 2 bếp 4 bàn, quái vật, kế hoạch ngày D1–D5, shop nâng cấp.<br>- Cài đặt vòng lặp `DaySim` kết nối 3 pha: gather → quan → shop.<br>- Hỗ trợ tham số `--days` và `--mode day` trong headless runner.<br>- Xử lý cơ chế tạm dừng (`pause`) đóng băng thời gian và đồng bộ snapshot. |
| **Trần Đức Trung** (`gather`) | Lát 1: Lặn & Sinh vật sông nước | `chonoi/sim/gather.py` | - Logic đàn cá: đổi hướng ngẫu nhiên tất định mỗi 120 tick, phản xạ tại biên, sinh cá mới ở tick 360 theo trọng số loài.<br>- Quái vật sông nước: cài đặt trạng thái Cá Sấu (tuần tra theo waypoint với vận tốc 1.0 m/s, phát hiện người chơi trong bán kính 10m và đuổi 2.0 m/s, cắn trừ 1 HP và rơi nửa giỏ theo LIFO, người chơi bất tử 90 tick, cá sấu giật lùi 60 tick). |
| **Đỗ Việt Anh** (`quan`) | Lát 2: Quán ăn đa bếp & Thực đơn ngày | `chonoi/sim/quan.py` | - Cập nhật không gian quán: quản lý 2 bếp nấu độc lập (`B1`, `B2`) và 4 bàn ăn (`T1`–`T4`).<br>- Xếp khách vào bàn trống có ID nhỏ nhất.<br>- Thực đơn 6 món chuẩn.<br>- Cơ chế gọi món: lọc món theo Kế hoạch ngày (`day_plan`), ưu tiên món còn chỉ tiêu trong ngày và kho khả dụng đủ nấu. |
| **Nguyễn Phi Hoàng** (`web`) | Client & UI Phase 2 | `chonoi/web/index.html`, `chonoi/web/` | - Mở rộng canvas hỗ trợ 2 bếp, 4 bàn và thực đơn mới.<br>- Hiển thị HUD Kế hoạch ngày, trạng thái đàn cá và cảnh báo cá sấu.<br>- Giao diện mua sắm Chợ Chú Sáu (`shop`) và phím bấm tạm dừng (Pause). |
| **Nguyễn Công Hoàn** (`qa`) | QA & Kiểm thử chấp nhận | `tests/test_phase2_qa.py`, `docs/verification/phase-2.md`, `docs/proof/phase-2/` | - Xây dựng bộ test chấp nhận `test_phase2_qa.py` bao phủ toàn bộ Acceptance Criteria của TICKET-02.<br>- Chạy regression tests Phase 1 và Phase 2.<br>- Kiểm tra tính tất định byte-by-byte qua skill `verify-phase` và xuất log bằng chứng. |

## 3. Rủi ro kỹ thuật & Giải pháp kiểm soát
1. **Rủi ro chuyển giao dữ liệu giữa các pha trong `DaySim`:**
   - *Giải pháp:* Hàng thu hoạch từ `gather` được kết xuất sang kho quán nguyên vẹn; doanh thu từ quán chuyển thành tiền khả dụng để mua sắm tại `shop`; nâng cấp ở `shop` được kích hoạt ngay đầu ngày kế tiếp.
2. **Rủi ro xung đột ID khi chạy nhiều ngày:**
   - *Giải pháp:* Dùng chung một thể hiện `IdAllocator` xuyên suốt các pha và các ngày để đảm bảo ID khách, đơn, vật phẩm không bao giờ trùng lặp.
3. **Rủi ro sai lệch tính tất định khi tạm dừng (`pause`):**
   - *Giải pháp:* Khi ở trạng thái `paused`, tách biệt `sim_tick` (tick hiển thị) và `phase_tick` (tick mô phỏng logic game); không tăng tick trò chơi và không gọi ngẫu nhiên từ `Streams` khi đang dừng.
