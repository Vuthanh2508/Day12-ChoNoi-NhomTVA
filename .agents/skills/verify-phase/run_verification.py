#!/usr/bin/env python3
"""Script kiểm chứng tự động cho từng phase (AI Skill: verify-phase).

Tác vụ:
1. Chạy toàn bộ test suites (python -m unittest discover -s tests -v).
2. Chạy headless simulation 2 lần cùng seed, băm SHA-256 để xác nhận tính tất định 100% byte-for-byte.
3. Xuất kết quả log thật vào docs/proof/phase-<N>/smoke_test.txt để dẫn chứng vào docs/verification/phase-<N>.md.
"""

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_tests():
    print("===> [1/3] Đang chạy bộ kiểm thử tự động (Unit & Smoke tests)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"tests{os.pathsep}."
    env["PYTHONUTF8"] = "1"
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    return p.returncode, p.stdout + p.stderr


def check_determinism():
    print("===> [2/3] Kiểm tra tính tất định byte-by-byte (cùng seed -> output giống nhau 100%)...")
    hashes = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in (1, 2):
            out_file = os.path.join(tmpdir, f"out_{i}.jsonl")
            cmd = [sys.executable, "-m", "chonoi.headless", "--mode", "gather", "--seed", "42",
                   "--ticks", "60", "--out", out_file]
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            if p.returncode != 0:
                return False, f"Headless failed with code {p.returncode}: {p.stderr}"
            with open(out_file, "rb") as f:
                hashes.append(hashlib.sha256(f.read()).hexdigest())

    is_identical = (hashes[0] == hashes[1])
    msg = f"Run 1 SHA256: {hashes[0]}\nRun 2 SHA256: {hashes[1]}\nTrùng khớp: {is_identical}"
    return is_identical, msg


def main():
    parser = argparse.ArgumentParser(description="Chạy kiểm chứng Phase và xuất bằng chứng.")
    parser.add_argument("--phase", type=int, default=1, help="Số thứ tự phase (1-4)")
    args = parser.parse_args()

    proof_dir = os.path.join(ROOT, "docs", "proof", f"phase-{args.phase}")
    os.makedirs(proof_dir, exist_ok=True)
    proof_log_path = os.path.join(proof_dir, "smoke_test.txt")

    test_code, test_output = run_tests()
    det_ok, det_msg = check_determinism()

    full_log = f"=== BẰNG CHỨNG KIỂM THỬ PHASE {args.phase} ===\n\n"
    full_log += f"--- 1. KẾT QUẢ UNIT & SMOKE TESTS (Mã thoát: {test_code}) ---\n"
    full_log += test_output + "\n\n"
    full_log += "--- 2. TÍNH TẤT ĐỊNH BYTE-FOR-BYTE ---\n"
    full_log += det_msg + "\n"

    with open(proof_log_path, "w", encoding="utf-8") as f:
        f.write(full_log)

    print(f"===> [3/3] Đã lưu log bằng chứng kiểm thử vào: {proof_log_path}")
    print("\n" + "=" * 50)
    if test_code == 0 and det_ok:
        print(f"✅ TẤT CẢ KIỂM CHỨNG PHASE {args.phase} ĐÃ ĐẠT!")
    else:
        print(f"⚠️ CÓ LỖI KIỂM THỬ TRONG PHASE {args.phase}. Vui lòng xem log chi tiết.")
    print("=" * 50)
    return 0 if (test_code == 0 and det_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
