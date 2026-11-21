"""Phase 4 / Contract v1.3: bench_cmd, soak_cmd, kế hoạch lặp D1–D5."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from chonoi.bench import metrics
from chonoi.contract import load_contract
from chonoi.soak import run_soak

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ContractV13Tests(unittest.TestCase):
    def test_declares_bench_and_soak(self):
        c = load_contract()
        self.assertEqual(c["contract_version"], "1.3")
        self.assertIn("chonoi.bench", c["bench_cmd"])
        self.assertIn("chonoi.soak", c["soak_cmd"])


class BenchMetricsTests(unittest.TestCase):
    def test_formulas(self):
        deltas = [10.0] * 98 + [50.0, 100.0]  # 100 khung: 1% chậm nhất = 1 khung 100 ms
        m = metrics(deltas, 1234.4)
        self.assertEqual(m["frames"], 100)
        self.assertAlmostEqual(m["measured_s"], 1.13, places=3)
        self.assertAlmostEqual(m["avg_fps"], 100 / 1.13, places=1)
        self.assertAlmostEqual(m["p1_low_fps"], 10.0, places=1)
        self.assertEqual(m["load_ms"], 1234)
        self.assertEqual(set(m), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})

    def test_p1_low_uses_ceil_of_one_percent(self):
        m = metrics([10.0] * 150 + [100.0, 100.0], 0)  # 152 khung -> ceil(1.52)=2 khung chậm nhất
        self.assertAlmostEqual(m["p1_low_fps"], 10.0, places=1)

    def test_cli_writes_five_fields(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "bench.json")
            env = {**os.environ, "PYTHONUTF8": "1", "CHONOI_BROWSER": os.path.join(d, "khong-co")}
            p = subprocess.run([sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "1", "--out", out],
                               cwd=ROOT, capture_output=True, text=True, env=env, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(data["frames"], 0)


class SoakTests(unittest.TestCase):
    def test_seven_days_cycle_plan_and_deterministic(self):
        a, b = run_soak(7, 6), run_soak(7, 6)  # 6 ngày: Ngày 6 phải dùng lại kế hoạch D1
        for r in (a, b):
            r.pop("duration_s")
        self.assertEqual(a, b)
        self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (6, 6, 0))
        self.assertEqual([r["day"] for r in a["results"]], [1, 2, 3, 4, 5, 6])
        self.assertEqual(set(a["results"][0]), {"day", "earned", "reputation", "score"})


if __name__ == "__main__":
    unittest.main()
