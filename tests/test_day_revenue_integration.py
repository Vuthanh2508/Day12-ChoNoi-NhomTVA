"""Integration test kiểm chứng toàn bộ vòng đời doanh thu và tiền tích lũy của DaySim qua nhiều ngày."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day import DaySim


NO_MOVE = (0.0, 0.0)


class DayRevenueIntegrationTests(unittest.TestCase):
    def test_multi_day_revenue_and_spending_lifecycle(self):
        """Kiểm chứng: Khách trả tiền -> DaySim nhận realtime -> Mua shop bị trừ tiền nhưng không giảm earned -> Sang Ngày 2 bảo toàn số dư và tính đúng shift_earned."""
        tuning = load_contract()["tuning"]
        # Vốn khởi đầu 150k
        scenario = {
            "day": {
                "day": 1,
                "money": 150,
                "earned": 0,
                "reputation": 3.0,
            },
            "gather": {
                "time_left_ticks": 5,  # Chuyển nhanh sang quán
                "hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100.0},
                    {"id": "I2", "kind": "bong_sung", "fresh": 100.0},
                    {"id": "I3", "kind": "ca_loc", "fresh": 100.0},
                    {"id": "I4", "kind": "bong_sung", "fresh": 100.0},
                ],
            },
            "quan": {
                "time_left_ticks": 60,
                "random_customers": False,
                # Đặt sẵn một khách đang ăn sắp xong để kiểm tra trả tiền
                "customers": [{
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "state": "eating",
                    "eat_ticks_left": 2,
                    "order_status": "served",
                    "base_price": 60,
                    "tip": 12,
                }],
            },
        }
        streams = Streams(42)
        ids = IdAllocator()
        sim = DaySim(tuning, scenario, streams, ids, days=2)

        # 1. Bắt đầu Ngày 1 - Pha gather
        self.assertEqual(sim.day, 1)
        self.assertEqual(sim.phase, "gather")
        self.assertEqual(sim.money, 150)
        self.assertEqual(sim.earned, 0)

        # Chạy hết 5 tick gather để sang quan
        for _ in range(5):
            sim.step(InputState(NO_MOVE, {}, set()))

        self.assertEqual(sim.phase, "quan")
        self.assertEqual(sim.sim_quan.money, 150)
        self.assertEqual(sim.sim_quan.earned, 0)
        self.assertEqual(sim.sim_quan.shift_earned, 0)

        # 2. Khách C1 ăn xong ở tick 2 của ca quán -> trả 60 + 12 = 72k
        evs = sim.step(InputState(NO_MOVE, {}, set()))
        self.assertEqual(sim.money, 150)  # eat_ticks_left còn 1

        evs = sim.step(InputState(NO_MOVE, {}, set()))
        # Khách trả tiền!
        paid_ev = [e for e in evs if e[0] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0][1]["amount"], 72)

        # Kiểm tra tiền và doanh thu cập nhật realtime trong DaySim từng tick
        self.assertEqual(sim.sim_quan.shift_earned, 72)
        self.assertEqual(sim.sim_quan.money, 222)
        self.assertEqual(sim.money, 222)
        self.assertEqual(sim.earned, 72)

        # Snapshot phản ánh đúng
        snap = sim.snapshot()
        self.assertEqual(snap["money"], 222)
        self.assertEqual(snap["earned"], 72)
        self.assertEqual(snap["shift_earned"], 72)

        # Chạy hết ca quán để sang shop
        while sim.phase == "quan":
            sim.step(InputState(NO_MOVE, {}, set()))

        self.assertEqual(sim.phase, "shop")
        self.assertEqual(sim.money, 222)
        self.assertEqual(sim.earned, 72)

        # 3. Mua nâng cấp Oxy cấp 1 (giá 200k)
        buy_evs = sim.step(InputState(NO_MOVE, {}, set(), raw={"buy": "oxygen"}))
        bought_ev = [e for e in buy_evs if e[0] == "bought"]
        self.assertEqual(len(bought_ev), 1)
        self.assertEqual(bought_ev[0][1]["price"], 200)

        # Số dư tiền bị trừ 200k còn 22k, nhưng tổng doanh thu earned vẫn nguyên vẹn 72k!
        self.assertEqual(sim.money, 22)
        self.assertEqual(sim.earned, 72)
        self.assertEqual(sim.upgrades["oxygen"], 1)

        # Đóng shop để sang Ngày 2
        sim.step(InputState(NO_MOVE, {}, {"shop_done"}))

        # 4. Bước sang Ngày 2
        self.assertEqual(sim.day, 2)
        self.assertEqual(sim.phase, "gather")
        # Bảo toàn số dư và doanh thu tích lũy xuyên ngày
        self.assertEqual(sim.money, 22)
        self.assertEqual(sim.earned, 72)

        # Chạy nhanh qua gather Ngày 2 sang quan Ngày 2
        # Setup hold Ngày 2 nếu cần
        sim.sim_gather.time_left_ticks = 1
        sim.step(InputState(NO_MOVE, {}, set()))
        self.assertEqual(sim.phase, "quan")

        # QuanSim Ngày 2 nhận đúng số dư 22k và earned 72k, nhưng shift_earned được reset về 0 cho ca mới!
        self.assertEqual(sim.sim_quan.money, 22)
        self.assertEqual(sim.sim_quan.earned, 72)
        self.assertEqual(sim.sim_quan.shift_earned, 0)

        # Khách Ngày 2 trả tiền: giả lập 1 đơn 72k
        sim.sim_quan.customers.append({
            "id": "C2",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "state": "eating",
            "eat_ticks_left": 1,
            "order_status": "served",
            "base_price": 60,
            "tip": 12,
        })
        sim.step(InputState(NO_MOVE, {}, set()))

        # Sau khi khách ngày 2 trả 72k:
        # Tiền: 22 + 72 = 94k
        # Doanh thu tích lũy: 72 + 72 = 144k
        # Doanh thu riêng ca Ngày 2: 72k
        self.assertEqual(sim.sim_quan.shift_earned, 72)
        self.assertEqual(sim.sim_quan.money, 94)
        self.assertEqual(sim.money, 94)
        self.assertEqual(sim.earned, 144)

        snap2 = sim.snapshot()
        self.assertEqual(snap2["money"], 94)
        self.assertEqual(snap2["earned"], 144)
        self.assertEqual(snap2["shift_earned"], 72)


if __name__ == "__main__":
    unittest.main()
