# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Vũ Thành | Setup cấu hình repo, thỏa thuận TEAM.md và 2 AI skills ban đầu | Chuẩn bị adapter kho `inventory.sample.json` | Cần chốt thứ tự nộp PR giữa Gather và Quán để tránh xung đột file snapshot khi merge |
| Phase 1 | Trần Đức Trung | Logic bơi, oxy, mất máu và ngạt nước cơ bản | Cài đặt hái cây và bắt cá lóc, cá linh | Phân vân về việc đặt tên trường payload trong sự kiện, cần đối chiếu chính xác với Contract B |
| Phase 1 | Đỗ Việt Anh | Đón khách và giữ chỗ nguyên liệu theo kho ban đầu | Cài đặt logic nấu bếp, phục vụ bàn và tính tiền | Chờ cấu trúc file kho chính thức từ Gather để kiểm tra tích hợp đầu-cuối |
| Phase 1 | Nguyễn Phi Hoàng | Dựng layout Canvas 2D và bảng điều khiển cơ bản | Vẽ HUD oxy, máu, giỏ và trạng thái bếp | Cần mock snapshot từ hai sim để vẽ giao diện độc lập không bị chặn |
| Phase 1 | Nguyễn Công Hoàn | Viết khung smoke test và kiểm tra schema | Mở rộng unit tests cho các trường hợp biên | Đang chờ code lát 1 và lát 2 ổn định để chạy kiểm thử hồi quy |
| Phase 2 | Vũ Thành | Nâng Contract v1.1, cài đặt vòng lặp `DaySim` và cờ `--days` | Tích hợp cơ chế tạm dừng `pause` vào `DaySim` | Nhánh `feat/gather-phase2` và `feat/quan-phase2` cùng sửa cấu trúc snapshot, cần yêu cầu các bạn rebase trước khi tạo PR |
| Phase 2 | Trần Đức Trung | Đàn cá bơi đổi hướng tất định và Cá Sấu tuần tra | Cài đặt Cá Sấu cắn mất máu và rơi đồ LIFO | Gặp merge conflict nhỏ khi gộp nhánh con do import trùng thư viện `Streams` |
| Phase 2 | Đỗ Việt Anh | Mở rộng không gian 2 bếp (`B1`, `B2`) và 4 bàn (`T1`–`T4`) | Cài đặt lọc món gọi theo Kế hoạch ngày D1–D5 | Phải đồng bộ lại thứ tự ưu tiên chọn bàn trống khi rebase với nhánh chính |
| Phase 2 | Nguyễn Phi Hoàng | Cập nhật HUD hiển thị ngày và cảnh báo Cá Sấu | Xây dựng giao diện Chợ Chú Sáu và màn hình Pause | Snapshot pha shop ban đầu bị thiếu trường metadata khi chạy kiểm thử thực tế |
| Phase 2 | Nguyễn Công Hoàn | Xây dựng bộ test chấp nhận `test_phase2_qa.py` | Kiểm tra tính tất định byte-by-byte qua skill `verify-phase` | Cần bổ sung fallback đường dẫn thực thi Python trên Windows để test không bị lỗi môi trường |
| Phase 3 | Vũ Thành | Nâng Contract v1.2, xây dựng schema kho cá thể và Dòng nước lũ | Tiến hành tích hợp PR #13 (gather) và PR #14 (quan) | Xung đột PR nghiêm trọng: PR #13 và PR #14 lệch kiểu biến `current_direction` (`int` vs `None`) gây crash tại `gather.py:677`, phải mở PR hotfix #15 giải quyết |
| Phase 3 | Trần Đức Trung | Cài đặt giỏ cá thể, hao tươi 0.5/s và Dòng lũ `current` | Viết bài test kiểm tra chu kỳ và lực đẩy dòng lũ | Conflict nhánh khi tích hợp cơ chế pause và hao tươi, bị đè phương thức xử lý ngạt oxy |
| Phase 3 | Đỗ Việt Anh | Hao tươi kho quán 0.25/s, phát hiện ươn `< 30` và giữ chỗ lại | Cài đặt chốt giá món theo độ tươi trung bình | Xung đột cấu trúc giữa dict đếm cũ và mảng cá thể mới, giải quyết bằng cách bọc lớp tương thích |
| Phase 3 | Nguyễn Phi Hoàng | Hiển thị độ tươi trên giao diện và cảnh báo ươn | Rà soát tương thích hiển thị Dòng nước lũ | Mạng cục bộ gặp sự cố gián đoạn không thể push nhánh riêng, phải chuyển sang pair programming cùng Integrator |
| Phase 3 | Nguyễn Công Hoàn | Cập nhật test suite Phase 3 với kho cá thể Contract G v1.2 | Kiểm tra tính tất định SHA-256 sau khi giải quyết xung đột | Test `test_inv_01` cũ bị fail vì Contract v1.2 từ chối kho đếm, phải đánh dấu lý do breaking change |
| Phase 4 | Vũ Thành | Hoàn thành `bench.py`, `soak.py`, Contract v1.3 và merge PR #16 | Hoàn thiện tài liệu nghiệm thu và chuẩn bị gắn tag | Cần rà soát toàn bộ cây làm việc đảm bảo mọi nhánh tính năng đã được merge sạch sẽ vào `main` |
| Phase 4 | Trần Đức Trung | Tối ưu hóa vòng lặp mô phỏng lặn cho benchmark FPS cao | Đảm bảo tính ổn định của giỏ đồ khi chạy soak dài ngày | Không gặp vướng mắc kỹ thuật |
| Phase 4 | Đỗ Việt Anh | Kiểm tra rò rỉ bộ nhớ và dọn rác đơn hàng cho soak 10 ngày | Hỗ trợ kiểm thử chế độ chơi live day | Không gặp vướng mắc kỹ thuật |
| Phase 4 | Nguyễn Phi Hoàng | Cài đặt chế độ tương phản cao và phụ đề SFX khi tắt tiếng | Bổ sung file phản tư cá nhân và nhật ký AI | Gặp conflict nhẹ trong `docs/members/` do đồng thời push tài liệu, đã pull và merge độc lập thành công |
| Phase 4 | Nguyễn Công Hoàn | Chạy toàn bộ 144/144 tests pass, trích xuất bằng chứng bench/soak | Cập nhật ma trận truy vết `docs/verification/phase-4.md` | Đạt 100% tiêu chí chấp nhận, sẵn sàng cho khâu phát hành Release v1.0.0 |
