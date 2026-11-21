# kientrungtd135 — Phản tư cá nhân

- **Tôi đã làm (kèm link commit):**

Phụ trách module Gather xuyên suốt Phase 1–3, gồm cơ chế lặn, oxy, thu hoạch, bắt cá, quái vật, quản lý giỏ cá thể, độ tươi và dòng nước lũ. Viết unit test, sửa lỗi tương thích contract và chạy regression đạt 115 PASS, 1 SKIPPED.

Các commit:
- Phase 1 — Gameplay: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/commit/f83333a814b692fb2ccb173eab101b5732ed83b2
- Phase 1 — Tests: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/commit/7783d403a85f9a5e7b889047a3dbac2451850612
- Phase 2 — Fish: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/commit/0f119964c64212c2a00cc6a5b8c36a070c2273d8
- Phase 2 — Gameplay: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/commit/3e92c5f0c655e1c954b98d71a653b54859fcbbcc
- Phase 3 — Inventory & Current: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/commit/7b19878194dbebe5767e676c455c74b2ad89cf97

- **Tôi đã review (kèm link):**

Đã kiểm tra code và test hồi quy của module Gather. Chưa có bằng chứng review PR của thành viên khác. PR dự kiến review: https://github.com/Vuthanh2508/Day12-ChoNoi-NhomTVA/pull/12

- **AI sai ở đâu và tôi phát hiện thế nào:**

AI sử dụng cấu trúc dữ liệu cũ khi chuyển sang inventory v1.2, khiến nhiều test thất bại. Tôi phát hiện qua traceback, đối chiếu contract và sửa code/test trước khi chạy lại regression.

- **Điều tôi học được:**

Hiểu quy trình phát triển theo phase, quản lý Git branch/PR, xử lý thay đổi contract và kiểm chứng code AI bằng unit test.
