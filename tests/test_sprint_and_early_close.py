import unittest
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.ids import IdAllocator
from chonoi.contract import load_contract


class SprintAndEarlyCloseTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.tuning = self.contract["tuning"]

    def test_gather_sprint_speed_multiplier(self):
        """Kiểm tra GatherSim tăng tốc độ bơi 1.6x khi có sprint."""
        streams1 = Streams(42)
        ids1 = IdAllocator()
        sim_normal = GatherSim(self.tuning, {"time_left_ticks": 600}, streams1, ids1)

        streams2 = Streams(42)
        ids2 = IdAllocator()
        sim_sprint = GatherSim(self.tuning, {"time_left_ticks": 600}, streams2, ids2)

        # Chạy 30 ticks với move ngang [1.0, 0.0]
        for _ in range(30):
            sim_normal.step(InputState([1.0, 0.0], {}, set(), raw={}))
            sim_sprint.step(InputState([1.0, 0.0], {}, set(), raw={"sprint": True}))

        # Vị trí x của sprint phải xa hơn rõ rệt (gấp xấp xỉ 1.6 lần quãng đường bình thường)
        dx_normal = sim_normal.pos[0] - 25.0
        dx_sprint = sim_sprint.pos[0] - 25.0
        self.assertGreater(dx_sprint, dx_normal * 1.5)

    def test_quan_sprint_speed_multiplier(self):
        """Kiểm tra QuanSim tăng tốc độ đi bộ 1.6x khi có sprint."""
        streams1 = Streams(42)
        ids1 = IdAllocator()
        sim_normal = QuanSim(self.tuning, {"time_left_ticks": 600}, streams1, ids1)

        streams2 = Streams(42)
        ids2 = IdAllocator()
        sim_sprint = QuanSim(self.tuning, {"time_left_ticks": 600}, streams2, ids2)

        # Chạy 30 ticks với move [1.0, 0.0]
        for _ in range(30):
            sim_normal.step(InputState([1.0, 0.0], {}, set(), raw={}))
            sim_sprint.step(InputState([1.0, 0.0], {}, set(), raw={"sprint": True}))

        dx_normal = sim_normal.pos[0] - 8.0
        dx_sprint = sim_sprint.pos[0] - 8.0
        self.assertGreater(dx_sprint, dx_normal * 1.5)

    def test_quan_early_close_10s_after_all_customers_done(self):
        """Kiểm tra điều kiện đóng ca sau 10s (600 ticks) khi hết khách theo kế hoạch ngày."""
        streams = Streams(42)
        ids = IdAllocator()
        scenario = {
            "day": 1,
            "time_left_ticks": 10000,
            "day_plan": [
                {"day": 1, "dishes": {"ca_kho_to": 1}}
            ],
            "stoves": [{"id": "B1", "pos": [2.0, 3.0]}],
            "tables": [{"id": "T1", "pos": [5.0, 3.0]}],
        }
        sim = QuanSim(self.tuning, scenario, streams, ids, mode="day")
        # Giả lập đã spawn xong món ca_kho_to và không còn khách
        sim.planned_dishes["ca_kho_to"] = 0
        sim.phase_tick = 120
        sim.customers = []
        sim.reservations = []

        events = sim.step(InputState([0.0, 0.0], {}, set()))
        self.assertTrue(sim._closing_soon)
        self.assertEqual(sim.time_left_ticks, 600)
        self.assertTrue(any(name == "all_customers_done" for name, _ in events))

        # Snapshot phản ánh closing_soon và time_left_ticks
        snap = sim.snapshot()
        self.assertTrue(snap["closing_soon"])
        self.assertEqual(snap["time_left_ticks"], 600)


if __name__ == "__main__":
    unittest.main()
