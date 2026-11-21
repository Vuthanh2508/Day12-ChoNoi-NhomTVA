# Đỗ Việt Anh (vietahnn) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đảm nhiệm vai trò PO & Dev Lead Quán (`sim/quan`), chịu trách nhiệm toàn bộ logic Quán xuyên suốt Phase 1–3:
    - Phase 1: Đón khách, giữ chỗ nguyên liệu, nấu bếp, bưng món, thanh toán, tip và điểm uy tín ([`816f957`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/816f957), [`9513bb6`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/9513bb6), [`8fbca65`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/8fbca65)).
    - Phase 2: Không gian 2 bếp B1/B2, 4 bàn T1–T4, menu 6 món chuẩn, lọc món theo `day_plan` D1–D5 ([`f52fa6a`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/f52fa6a), [`58bb1ae`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/58bb1ae)).
    - Phase 3: Kho cá thể `{id, kind, fresh}`, hao tươi 0.25/s, event `spoiled`, giữ cá thể tươi nhất, re-reserve khi ươn / unfulfillable, chốt `base_price` theo độ tươi trung bình, xử lý khách đặt trước reservations ([`f64d312`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/f64d312), [`5c00e39`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/5c00e39)).
    - Quản lý và làm rõ các điều khoản 1, 6–15 trong [docs/clarify.md](../clarify.md) trong vai trò PO.
- **Tôi đã review (kèm link):**
  - Rà soát hợp đồng bàn giao nguyên liệu giữa Gather và Quán, kiểm tra tương thích ngược giữa các Phase ([PR #13](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/pull/13), [PR #14](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/pull/14)).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI áp dụng hao tươi trực tiếp lên kho khiến các test cũ dùng dict của Phase 1 bị lỗi `AttributeError`; phát hiện qua test runner và xử lý bằng lớp `StockList` tương thích ngược.
  - AI tính tiền boa theo giá niêm yết thay vì trên `base_price` đã chốt theo độ tươi trung bình; phát hiện khi đối chiếu contract Phase 3 và viết test kiểm chứng.
- **Điều tôi học được:**
  - Tầm quan trọng của việc duy trì tính tương thích ngược khi tiến hóa contract; kỹ năng chốt sớm các trường hợp biên qua `clarify.md` giúp team phát triển song song hiệu quả.
