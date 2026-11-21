"""Acceptance tests for Phase 3 / inventory contract v1.2.

These tests intentionally exercise the public contract through the headless
runner so that the same fixtures can be used for the integrated build.
"""

import json
import math
import os
import tempfile
import unittest

from chonoi.contract import load_contract

try:
    from helpers import events, read_jsonl, run_headless, snapshots, write_json
except ImportError:  # pragma: no cover - direct discovery from repository root
    from tests.helpers import events, read_jsonl, run_headless, snapshots, write_json


class Phase3InventoryAndCurrentQATests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def run_cli(self, mode, ticks, **args):
        out = self.path("run.jsonl")
        command = ["--mode", mode, "--seed", "42", "--ticks", str(ticks), "--out", out]
        for flag, value in args.items():
            command.extend(["--" + flag.replace("_", "-"), str(value)])
        code, stderr = run_headless(*command)
        return code, stderr, read_jsonl(out) if code == 0 else []

    def test_v12_inventory_accepts_individuals_and_rejects_legacy_counts(self):
        # v1.3 (Phase 4) giữ nguyên gameplay/tuning/kho/JSONL của v1.2, chỉ thêm bench_cmd/soak_cmd
        self.assertEqual(load_contract()["contract_version"], "1.3")

    def test_inventory_file_accepts_individual_item_schema(self):
        valid = self.path("individuals.json")
        write_json(valid, {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 97.5}]})
        code, stderr, rows = self.run_cli("quan", 0, inventory=valid)
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(snapshots(rows)[0]["stock"], [{"id": "I1", "kind": "ca_linh", "fresh": 97.5}])

    def test_inventory_file_rejects_legacy_count_schema_with_exit_two(self):
        legacy = self.path("legacy-counts.json")
        write_json(legacy, {"items": {"ca_linh": 1}})
        code, _, _ = self.run_cli("quan", 0, inventory=legacy)
        self.assertEqual(code, 2)

    def test_freshness_decay_rates_and_pause_freezes_stock(self):
        freshness = load_contract()["tuning"]["freshness"]
        self.assertEqual(freshness["gather_decay_per_s"], 0.5)
        self.assertEqual(freshness["quan_decay_per_s"], 0.25)
        scenario = self.path("paused-stock.json")
        write_json(scenario, {"quan": {"stock": [{"id": "I1", "kind": "ca_linh", "fresh": 80}],
                                       "random_customers": False}})
        inputs = self.path("pause.json")
        write_json(inputs, {"frames": [{"tick": 0, "pause": True}]})
        code, stderr, rows = self.run_cli("quan", 4, scenario=scenario, inputs=inputs, snapshot_every=1)
        self.assertEqual((code, stderr), (0, ""))
        frozen = [s for s in snapshots(rows) if s["state"] == "paused"]
        self.assertTrue(frozen)
        self.assertTrue(all(frozen_item["stock"][0]["fresh"] == 80 for frozen_item in frozen))

    def test_inventory_freshness_manifest_values(self):
        freshness = load_contract()["tuning"]["freshness"]
        self.assertEqual(freshness["gather_decay_per_s"], 0.5)
        self.assertEqual(freshness["quan_decay_per_s"], 0.25)

    def test_item_at_spoil_threshold_emits_one_event_on_boundary_tick(self):
        scenario = self.path("spoils.json")
        write_json(scenario, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                                         "random_fish": False}})
        code, stderr, rows = self.run_cli("gather", 4, scenario=scenario)
        self.assertEqual((code, stderr), (0, ""))
        spoiled = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in spoiled], [(1, "I1")])

    def test_spoiled_reserved_item_retries_with_freshest_valid_id(self):
        scenario = self.path("reservation-retry.json")
        write_json(scenario, {"quan": {
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_loc", "fresh": 95},
                {"id": "I3", "kind": "ca_loc", "fresh": 90},
            ],
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "order_status": "reserved", "reserved": ["I1"]}],
        }})
        code, stderr, rows = self.run_cli("quan", 2, scenario=scenario, snapshot_every=1)
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(len(events(rows, "spoiled")), 1)
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["I1"])
        self.assertEqual(snapshots(rows)[1]["customers"][0]["reserved"], ["I2"])

    def test_price_uses_average_freshness_and_tip_is_calculated_after_price(self):
        scenario = self.path("fresh-price.json")
        write_json(scenario, {"quan": {
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 80},
            ],
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "eating", "eat_ticks_left": 1, "patience_ticks_left": 3600,
                           "freshness": [80]}],
        }})
        code, stderr, rows = self.run_cli("quan", 2, scenario=scenario, snapshot_every=1)
        self.assertEqual((code, stderr), (0, ""))
        paid = events(rows, "paid")
        self.assertTrue(paid)
        # Contract price is floor(base menu price * mean freshness / 100); the
        # quick-service tip is then floor(fresh-adjusted price * tip_rate).
        self.assertEqual(paid[-1]["data"]["base_price"], math.floor(60 * 0.8))
        self.assertEqual(paid[-1]["data"]["tip"], math.floor(48 * 0.2))

    def test_gather_file_handoff_is_atomic_and_day_handoff_preserves_freshness(self):
        scenario = self.path("handoff.json")
        write_json(scenario, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                         "random_fish": False, "time_left_ticks": 1}})
        inputs = self.path("dock.json")
        write_json(inputs, {"frames": [{"tick": 0, "interact": True}]})
        inventory = self.path("inventory.json")
        code, stderr, rows = self.run_cli("gather", 1, scenario=scenario, inputs=inputs, inventory_out=inventory)
        self.assertEqual((code, stderr), (0, ""))
        with open(inventory, encoding="utf-8") as inventory_file:
            saved = json.load(inventory_file)
        self.assertEqual(saved["items"][0]["id"], "I1")
        self.assertAlmostEqual(saved["items"][0]["fresh"], 100 - 0.5 / 60, delta=0.01)
        code, stderr, quan_rows = self.run_cli("quan", 0, inventory=inventory)
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(snapshots(quan_rows)[0]["stock"], saved["items"])
        day_scenario = self.path("day.json")
        write_json(day_scenario, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                             "random_fish": False, "time_left_ticks": 1},
                                  "quan": {"random_customers": False}})
        code, stderr, day_rows = self.run_cli("day", 2, scenario=day_scenario, snapshot_every=1)
        self.assertEqual((code, stderr), (0, ""))
        quan_snapshots = [s for s in snapshots(day_rows) if s["phase"] == "quan"]
        self.assertTrue(quan_snapshots)
        self.assertEqual(quan_snapshots[0]["stock"], saved["items"])

    def test_current_warns_at_lead_boundary_and_pushes_at_depth_ten(self):
        self.assertIn("current", load_contract()["tuning"]["gather"])
        current = load_contract()["tuning"]["gather"]["current"]
        self.assertEqual(current["warning_ticks"], 120)
        self.assertEqual(current["duration_ticks"], 480)
        self.assertEqual(current["min_depth"], 10)
        self.assertEqual(current["speed"], 1.5)
        scenario = self.path("current.json")
        write_json(scenario, {"gather": {"player": {"pos": [50, 10]}, "random_fish": False,
                                         "monsters": [],
                                         "current_direction": 1}})
        start = current["interval_ticks"]
        code, stderr, rows = self.run_cli("gather", start + 1, scenario=scenario, snapshot_every=1)
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual([e["tick"] for e in events(rows, "current_warning")], [start - current["warning_ticks"]])
        before = [s for s in snapshots(rows) if s["tick"] == start - 1][-1]
        first = [s for s in snapshots(rows) if s["tick"] == start][-1]
        self.assertAlmostEqual(first["player"]["pos"][0] - before["player"]["pos"][0], 1.5 / 60, delta=0.01)

        # Start at the surface so oxygen lasts through the entire current.
        write_json(scenario, {"gather": {"player": {"pos": [50, 0]}, "random_fish": False,
                                         "monsters": [], "current_direction": -1}})
        inputs = self.path("dive.json")
        write_json(inputs, {"frames": [{"tick": start, "move": [0, 1]}]})
        end = start + current["duration_ticks"]
        code, stderr, rows = self.run_cli("gather", end, scenario=scenario, inputs=inputs, snapshot_every=1)
        self.assertEqual(code, 0, stderr)
        states = snapshots(rows)
        for tick in range(start, end):
            state = states[tick]
            self.assertEqual(state["current"], {"direction": -1, "ticks_left": end - tick})
            x, depth = state["player"]["pos"]
            expected = -current["speed"] / 60 if depth >= current["min_depth"] else 0
            self.assertAlmostEqual(x - states[tick - 1]["player"]["pos"][0], expected, delta=0.001)
        self.assertIsNone(states[end]["current"])
        self.assertEqual(states[end]["player"]["pos"][0], states[end - 1]["player"]["pos"][0])

    def test_current_manifest_contract_values(self):
        self.assertIn("current", load_contract()["tuning"]["gather"])
        current = load_contract()["tuning"]["gather"]["current"]
        self.assertEqual((current["warning_ticks"], current["duration_ticks"], current["min_depth"], current["speed"]),
                         (120, 480, 10, 1.5))


if __name__ == "__main__":
    unittest.main()
