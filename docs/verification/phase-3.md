# Kiểm chứng Phase 3 · Contract v1.2

Bản QA tích hợp main sau PR #15 (sửa code trùng do merge #13/#14) và Quán `5c00e39`. Chạy `python .agents/skills/verify-phase/run_verification.py --phase 3` cho kết quả **135/135 đạt**. [Log regression và SHA-256](../proof/phase-3/smoke_test.txt)

| AC | Ca kiểm chứng đạt |
|---|---|
| AC-P3-01 · Schema | Kho cá thể hợp lệ đọc lại được. Kho đếm cũ, ID trùng, kind lạ và độ tươi ngoài miền bị từ chối. |
| AC-P3-02 · Độ tươi | Kiểm tra hao tươi ở bước gather bàn giao, hao tươi kho quán và pause. |
| AC-P3-03 · Ngưỡng 30 | Gather bắt đầu ở 30, phát đúng một spoiled tại tick 1 trong bốn bước quan sát. |
| AC-P3-04 · Giữ nguyên liệu | Khách giữ I1 trước khi ươn, sau đó giữ I2 tươi nhất trong kho còn lại. |
| AC-P3-05 · Giá và tip | Kiểm tra cook_started, giá theo trung bình độ tươi và tip theo giá đã chốt trong test_quan_freshness. |
| AC-P3-06 · Bàn giao | So file kho với gather_end, snapshot quán ở tick 0 và kho trong day ngay lúc chuyển pha. Giới hạn tick trước khi kết thúc giữ nguyên file đích. |
| AC-P3-07 · Dòng lũ | Kiểm tra tick cảnh báo, lực đẩy ở độ sâu 10, toàn bộ 480 tick hoạt động, vùng nông và tick kết thúc. |
| HUD | Edge headless, canvas 1280×720, fixture hold/stock. Kiểm tra chữ vẽ cho I1 ở 30.0% và I2 ở 29.5% có nhãn ƯƠN ở cả gather và quan. Đây là phép thử HUD bằng fixture. |
| Tính tất định | Hai lượt Gather cùng seed 42, 60 tick có SHA-256 trùng nhau. |
