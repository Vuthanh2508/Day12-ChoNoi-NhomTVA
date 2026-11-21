"""Kiểm thử tham số độ tươi (freshness) được đọc động từ tuning/contract (không hard-code)."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim


class FreshnessConfigTests(unittest.TestCase):
    def setUp(self):
        self.base_contract = load_contract()

    def test_gather_uses_tuning_freshness_config(self):
        """GatherSim áp dụng đúng initial, gather_decay_per_s, spoiled_below từ tuning."""
        tuning = dict(self.base_contract["tuning"])
        tuning["freshness"] = {
            "initial": 95.0,
            "gather_decay_per_s": 1.2,  # 1.2 / 60 = 0.02 mỗi tick
            "spoiled_below": 45.0,
        }
        # Vật phẩm có độ tươi 45.03, sau 2 tick (mỗi tick giảm 0.02) sẽ xuống 44.99 < 45.0 -> spoiled
        scenario = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 45.03}],
            "random_fish": False,
            "time_left_ticks": 60,
        }
        streams = Streams(42)
        ids = IdAllocator()
        sim = GatherSim(tuning, scenario, streams, ids, individual_items=True)
        inp = InputPlayer([])

        self.assertEqual(sim.fresh_initial, 95.0)
        self.assertAlmostEqual(sim.fresh_decay_per_tick, 1.2 / 60.0)
        self.assertEqual(sim.fresh_spoiled_below, 45.0)

        # Tick 1: 45.03 - 0.02 = 45.01 >= 45.0 (chưa ươn)
        ev1 = sim.step(inp.advance(0))
        self.assertFalse(any(e[0] == "spoiled" for e in ev1))
        self.assertAlmostEqual(sim.hold[0]["fresh"], 45.01)

        # Tick 2: 45.01 - 0.02 = 44.99 < 45.0 (phát hiện ươn theo ngưỡng mới 45.0)
        ev2 = sim.step(inp.advance(1))
        spoiled_evs = [e for e in ev2 if e[0] == "spoiled"]
        self.assertEqual(len(spoiled_evs), 1)
        self.assertEqual(spoiled_evs[0][1]["item_id"], "I1")

    def test_quan_uses_tuning_freshness_config(self):
        """QuanSim áp dụng đúng initial, quan_decay_per_s, spoiled_below từ tuning."""
        tuning = dict(self.base_contract["tuning"])
        tuning["freshness"] = {
            "initial": 90.0,
            "quan_decay_per_s": 0.6,  # 0.6 / 60 = 0.01 mỗi tick
            "spoiled_below": 50.0,
        }
        # Kho có I1: 50.015, sau 2 tick giảm còn 49.995 < 50.0 -> spoiled
        # Kho có I2: 48.0 < 50.0 (không đủ chuẩn nấu theo ngưỡng mới)
        scenario = {
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 50.015},
                {"id": "I2", "kind": "ca_loc", "fresh": 48.0},
            ],
            "random_customers": False,
            "time_left_ticks": 60,
        }
        streams = Streams(42)
        ids = IdAllocator()
        sim = QuanSim(tuning, scenario, streams, ids)
        inp = InputPlayer([])

        self.assertEqual(sim.fresh_initial, 90.0)
        self.assertAlmostEqual(sim.fresh_decay_per_tick, 0.6 / 60.0)
        self.assertEqual(sim.fresh_spoiled_below, 50.0)

        # Kiểm tra ngưỡng giữ chỗ không nhận I2 vì fresh < 50.0
        selected = sim._reserve_items_for_dish("ca_loc_nuong_trui")
        self.assertEqual(selected, ["I1"])  # Chỉ có I1 đủ điều kiện >= 50.0

        # Tick 1: 50.015 - 0.01 = 50.005 >= 50.0
        ev1 = sim.step(inp.advance(0))
        # Chú ý: I2 vốn đã < 50.0 nên bị phát hiện spoiled ngay ở tick 1
        spoiled_i2 = [e for e in ev1 if e[0] == "spoiled" and e[1]["item_id"] == "I2"]
        self.assertEqual(len(spoiled_i2), 1)

        # Tick 2: I1 giảm xuống 50.005 - 0.01 = 49.995 < 50.0 -> phát hiện spoiled
        ev2 = sim.step(inp.advance(1))
        spoiled_i1 = [e for e in ev2 if e[0] == "spoiled" and e[1]["item_id"] == "I1"]
        self.assertEqual(len(spoiled_i1), 1)


if __name__ == "__main__":
    unittest.main()
