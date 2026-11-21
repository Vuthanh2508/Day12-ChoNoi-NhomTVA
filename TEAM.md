# TEAM

**Tên nhóm:** NhomTVA  **Số người:** 5  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trần Đức Trung | kientrungtd135 | `sim/gather` | Dev Lead (Gather) | Đỗ Việt Anh (`sim/quan`) |
| Đỗ Việt Anh | vietahnn | `sim/quan` | PO (Product Owner) | Trần Đức Trung (`sim/gather`) |
| Nguyễn Phi Hoàng | phihoang1709  | `chonoi/web` | UI Lead / Frontend | Nguyễn Công Hoàn (`qa`) |
| Nguyễn Công Hoàn | hoan11052004 | `qa` | QA Lead | Nguyễn Phi Hoàng (`chonoi/web`) |
| Vũ Thành | Vuthanh2508 | `integration` | Integrator / Release | Cả nhóm (hỗ trợ tích hợp) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Discord / Face to face tại lớp
- Khi bất đồng về thiết kế: Thảo luận tối đa 5 phút, nếu không chốt được, PO và Integrator quyết định dựa trên PRD và ghi lại lý do vào `docs/clarify.md`.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay lên kênh Discord, người dự phòng cùng AI hỗ trợ gỡ lỗi hoặc nhận lại lát việc để đảm bảo mốc tag.
- Giờ standup giữa phase: Họp nhanh 2-3 phút tại các mốc: 0:30 (giữa Phase 1), 1:30 (giữa Phase 2), 2:15 (giữa Phase 3)
- Cách đọc code của nhau (tùy chọn): Review chéo theo cặp module liền kề (`sim/gather` đọc `sim/quan`, QA đọc cả hai); kiểm tra nhanh trước khi merge nhánh
- Cách làm việc với Git: Mỗi người làm trên nhánh riêng (hoặc chia file rõ ràng), tự chạy test pass ở local trước khi gộp vào main, Integrator là người duy nhất kiểm tra và gắn tag `phase-n`
