# Nguyễn Phi Hoàng (phihoang1709) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Client `chonoi/web/index.html` (vai UI Lead, commit [`f9e7bd0`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/f9e7bd0)): HUD gather (oxy/máu/giỏ + vector hình riêng từng loại cá/hoa), quán states (bếp Trống/nấu/chín, bàn + khách chờ/đang ăn, panel tiền/uy tín), HUD chuẩn P2 (chữ ≥18px, checklist "Má Tư cần", cảnh báo "Thủy quái!"/"Hết hơi!"), màn hình vòng ngày (Menu/DayIntro/Shop/Pause), reskin miền Tây (Út Sen áo bà ba – khăn rằn – kính lặn, đèn dây vàng, khói bếp, phù sa – dừa nước), thoại Nam Bộ + SFX WebAudio.
- **Tôi đã review (kèm link):**
  - Rà lại `index.html` sau các merge phase 3/4 (kiểm tra HUD/reskin còn nguyên, 143 tests OK).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI định hard-code giá/cook_s từ `tuning.menu` — đối chiếu snapshot `GET /state` thấy `meta` chỉ chứa `tuning[mode]`, nên tách nhãn hiển thị khỏi số liệu.
  - Hook Mimosa chặn commit vì report lỗi ở file khung; đọc code bị flag thấy là false-positive (test localhost, RNG có seed) thay vì sửa test cho xanh.
- **Điều tôi học được:**
  - Client render phòng thủ (sim có tới đâu hiện tới đó) giúp UI đi song song sim không chặn nhau; verify UI bằng mock-snapshot trước khi sim kịp implement.
