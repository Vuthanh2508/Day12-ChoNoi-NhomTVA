# Vũ Thành (Vuthanh2508) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Vai trò Integrator & Release Lead xuyên suốt 4 phase:
    - P1: Setup repo, `TEAM.md`, `game.contract.json` v1.0, 2 AI skills (`verify-phase`, `inventory-validator`) ([`ecb02ca`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/ecb02ca)).
    - P2: Cài đặt vòng lặp `DaySim` kết nối 3 pha (gather → quan → shop), CLI `--days` ([`0d0b00f`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/0d0b00f)).
    - P3: Nâng Contract v1.2, adapter kho cá thể ([`5ba2b0b`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/5ba2b0b)), giải quyết merge conflict PR #15 ([`39c3bd3`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/39c3bd3)).
    - P4: Nâng Contract v1.3, cài đặt `bench.py`, `soak.py` ([`0eff058`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/0eff058)), cơ chế Sprint Shift, đóng ca 10s ([`7b7502e`](https://github.com/Vuthanh2508/K5-L3B-LAB-Day12-AI-SDLC-NhomTVA/commit/7b7502e)) và hoàn thiện Release v1.0.0.
- **Tôi đã review (kèm link):**
  - Rà soát hợp đồng và merge 16 PRs của cả nhóm (PR #4, #6, #7, #8, #9, #10, #13, #14, #16).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI từng ép kiểu `int(reputation)` làm mất điểm thập phân và trừ hao tươi khi pause; tôi phát hiện qua `test_phase4.py` và sửa lại.
- **Điều tôi học được:**
  - Phát triển hướng hợp đồng (Contract-driven) và tự động hóa kiểm thử tính tất định là chìa khóa để 5 người làm song song hiệu quả.
