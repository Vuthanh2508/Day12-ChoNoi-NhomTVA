"""Chế độ day trên máy chủ live: chơi trọn ngày (sáng -> quán có khách -> shop -> ngày sau) và HTTP."""
import json
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer

TUNING = load_contract()["tuning"]
HOLD = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100},
        {"id": "I3", "kind": "bong_sung", "fresh": 100}]
SCEN = {"gather": {"time_left_ticks": 120, "hold": HOLD}}


class LiveDayTests(unittest.TestCase):
    def test_full_two_days_with_customers_and_shop(self):
        g = LiveGame("day", TUNING, SCEN, 1, days=2)
        phases, names = [], set()
        while not g.session.done and g.session.tick < 60 * 400:
            sim = g.session.sim
            if sim.phase == "shop" and sim.phase_tick == 5:
                g.set_input({"buy": "oxygen"})
                g.set_input({"shop_done": True})
            g._tick_once()
            names.update(e["name"] for e in g.events)
            if not phases or phases[-1] != (sim.day, sim.phase):
                phases.append((sim.day, sim.phase))
            json.loads(g.state_json())  # snapshot không được văng lỗi ở mọi pha (kể cả shop)
        self.assertEqual(phases, [(1, "gather"), (1, "quan"), (1, "shop"),
                                  (2, "gather"), (2, "quan"), (2, "shop")])
        self.assertTrue({"customer_arrived", "day_start", "shop_end"} <= names)
        self.assertEqual(g.session.sim.reason, "days_complete")

    def test_pause_is_a_toggle_and_freezes_ticks(self):
        g = LiveGame("day", TUNING, SCEN, 1, days=1)
        g._tick_once()
        g.set_input({"pause": True})
        g._tick_once()
        t = g.session.sim.sim_tick
        g.set_input({"move": [0, 0]})  # client không gửi lại pause => vẫn đang tạm dừng
        for _ in range(30):
            g._tick_once()
        self.assertEqual(g.session.sim.sim_tick, t)
        g.set_input({"pause": True})
        g._tick_once()
        g._tick_once()
        self.assertGreater(g.session.sim.sim_tick, t)

    def test_http_state_and_input_v11_fields(self):
        g = LiveGame("day", TUNING, SCEN, 1, days=1)
        srv = LiveServer(g, port=0)
        srv.start()
        try:
            body = json.dumps({"move": [0, 0], "pause": True, "buy": "oxygen", "shop_done": False}).encode()
            req = urllib.request.Request(srv.url + "input", data=body, method="POST")
            self.assertEqual(urllib.request.urlopen(req).status, 200)
            st = json.loads(urllib.request.urlopen(srv.url + "state").read())
            self.assertEqual(st["mode"], "day")
            self.assertIn("upgrades", st["meta"])
            self.assertIn("menu", st["meta"])
        finally:
            srv.stop()


if __name__ == "__main__":
    unittest.main()
