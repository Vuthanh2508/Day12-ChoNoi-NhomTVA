"""Buổi tối — Mở Quán.

PRD-0 mục F & Phase 3 (Quán / Bếp & Độ tươi):
  Lát 2 Phase 3:
    - Quản lý kho quán cá thể:
      + Tiếp nhận s.stock dạng mảng cá thể {id, kind, fresh}.
      + Hao tươi kho quán: giảm 0.25 điểm/s (mỗi tick giảm 0.25/60, kẹp đáy 0, dừng khi pause).
      + Phát event spoiled {item_id, kind, location: "stock"} theo id khi fresh < 30.
    - Giữ chỗ & Nấu theo cá thể:
      + Thay thế giữ theo lượng thành giữ theo id: Chọn các cá thể khả dụng tươi nhất (fresh cao nhất, nếu bằng nhau thì theo id nhỏ).
      + Xử lý ươn khi đang giữ chỗ: Nếu cá thể đang giữ bị rơi xuống < 30, nhả toàn bộ phần giữ của đơn và thử giữ lại đúng 1 lần. Nếu thiếu thì chuyển unfulfillable.
      + Chốt giá món: base_price = floor(giá niêm yết * trung bình fresh của các cá thể nấu / 100). Tiền boa = floor(tiền món * 0.2) trên giá đã chốt.
      + Sự kiện cook_started: data.items là mảng cá thể sắp xếp theo kind rồi theo id.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
FRESH_DECAY_PER_TICK = 0.25 / TICK


class StockList(list):
    """List các cá thể kho, hỗ trợ get(kind, default=0) để backward-compatible."""
    def get(self, kind, default=0):
        cnt = sum(1 for it in self if isinstance(it, dict) and it.get("kind") == kind)
        return cnt if cnt > 0 else default


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, mode=None):
        self.mode = mode or scenario.get("mode", "quan")
        self.phase = "quan"
        self.tuning = tuning
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.phase_tick = scenario.get("phase_tick", 0)
        self.day = scenario.get("day", 1)
        self.paused = bool(scenario.get("paused", False))
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # Kho quán cá thể: tiếp nhận mảng cá thể [{id, kind, fresh}, ...]
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        self._legacy_stock = isinstance(raw_stock, dict)
        self.stock = StockList()
        if isinstance(raw_stock, list):
            for it in raw_stock:
                ids.reserve(it["id"])
                self.stock.append({
                    "id": it["id"],
                    "kind": it["kind"],
                    "fresh": float(it.get("fresh", 100.0)),
                })
        elif isinstance(raw_stock, dict):
            for k in sorted(raw_stock.keys()):
                for _ in range(raw_stock[k]):
                    item_id = ids.new("I")
                    self.stock.append({
                        "id": item_id,
                        "kind": k,
                        "fresh": 100.0,
                    })
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0),
                            order_id=s.get("order_id"), base_price=s.get("base_price", 0),
                            items=s.get("items", []))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.random_customers = scenario.get("random_customers", True)

        # Kế hoạch ngày (day_plan) cho mode day
        day_plans = scenario.get("day_plan") or tuning.get("day_plan", [])
        self.day_plan = next((dp for dp in day_plans if dp.get("day") == self.day), None)
        if self.day_plan:
            self.planned_dishes = dict(self.day_plan.get("dishes", {}))
        else:
            self.planned_dishes = None

        for s in self.stoves:
            ids.reserve(s["id"])
        for tb in self.tables:
            ids.reserve(tb["id"])

        self.customers = []
        patience_max = int(round(t["patience_s"] * 60))
        for c in scenario.get("customers", []):
            ids.reserve(c["id"])
            dish_id = c.get("dish_id") or c.get("dish")
            listed_price = self.menu[dish_id]["price"] if (dish_id and dish_id in self.menu) else 0
            if "freshness" in c and c["freshness"]:
                avg_fresh = sum(c["freshness"]) / len(c["freshness"])
                base_price = math.floor(listed_price * avg_fresh / 100.0)
            elif "base_price" in c:
                base_price = c["base_price"]
            else:
                base_price = listed_price
            order_status = c.get("order_status", "served" if c.get("state") == "eating" else "reserved")

            raw_res = c.get("reserved", c.get("reserved_ids", []))
            if isinstance(raw_res, list):
                reserved_ids = list(raw_res)
            elif isinstance(raw_res, dict) and dish_id in self.menu:
                reserved_ids = self._reserve_items_for_dish(dish_id) or []
            elif order_status == "reserved" and dish_id in self.menu:
                reserved_ids = self._reserve_items_for_dish(dish_id) or []
            else:
                reserved_ids = []

            if self._legacy_stock and dish_id in self.menu:
                reserved_val = dict(self.menu[dish_id]["recipe"])
            else:
                reserved_val = list(reserved_ids)

            tip = c.get("tip")
            if tip is None:
                ratio = c.get("patience_ticks_left", patience_max) / patience_max
                if c.get("state") == "eating" and ratio >= t["tip_min_patience_ratio"]:
                    tip = math.floor(base_price * t["tip_rate"])
                else:
                    tip = 0

            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": dish_id,
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", patience_max),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": order_status,
                "reserved_ids": reserved_ids,
                "reserved": reserved_val,
                "base_price": base_price,
                "tip": tip,
            }
            self.customers.append(cust)

        # Khớp bếp với khách assigned nếu chưa có order_id
        for c in self.customers:
            if c["order_status"] == "assigned":
                if not (self.hand and self.hand.get("order_id") == c["id"]):
                    for s in self.stoves:
                        if s["state"] in ("cooking", "ready") and s["dish"] == c["dish_id"] and not s.get("order_id"):
                            s["order_id"] = c["id"]
                            s["base_price"] = c["base_price"]
                            break

        self.money = int(scenario.get("money", 0))
        self.earned = int(scenario.get("earned", 0))
        self.shift_earned = 0
        self.done = False
        self.reason = None

        self.reservations = [dict(r) for r in scenario.get("reservations", [])]
        for r in self.reservations:
            ids.reserve(r["id"])

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _reserve_items_for_dish(self, dish_id, excluded_ids=None):
        """Chọn các cá thể khả dụng tươi nhất (fresh cao nhất, nếu bằng nhau thì theo id nhỏ)."""
        if excluded_ids is None:
            excluded_ids = set()
            for cust in self.customers:
                for iid in cust.get("reserved_ids", []):
                    excluded_ids.add(iid)

        recipe = self.menu[dish_id]["recipe"]
        selected_ids = []
        for kind, qty in sorted(recipe.items()):
            available = [it for it in self.stock
                         if it["kind"] == kind and it["fresh"] >= 30.0 and it["id"] not in excluded_ids and it["id"] not in selected_ids]
            if len(available) < qty:
                return None
            # Sắp xếp: fresh cao nhất (-it["fresh"] nhỏ nhất), nếu bằng nhau thì id nhỏ hơn
            available.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
            for it in available[:qty]:
                selected_ids.append(it["id"])
        return selected_ids

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        if self._legacy_stock:
            stock_snap = {}
            for it in self.stock:
                stock_snap[it["kind"]] = stock_snap.get(it["kind"], 0) + 1
            stock_snap = {k: stock_snap[k] for k in sorted(stock_snap) if stock_snap[k] > 0}
        else:
            stock_snap = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
                          for it in sort_by_id(self.stock)]
        return {
            "player": {"pos": self.pos},
            "stock": stock_snap,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
            "money": self.money,
            "earned": self.earned,
            "shift_earned": self.shift_earned,
            "reputation": self.reputation,
        }

    def step(self, inp):
        events = []

        # Xử lý nút pause
        if hasattr(inp, "held") and "pause" in inp.held:
            is_held = inp.held["pause"]
            if is_held != self.paused:
                self.paused = is_held
                events.append(("paused", {}) if self.paused else ("resumed", {}))
        elif hasattr(inp, "pressed") and inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("paused", {}) if self.paused else ("resumed", {}))

        if self.paused:
            return events

        self.phase_tick += 1

        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1

        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)

        # Hao tươi kho quán: giảm 0.25 điểm/s (mỗi tick giảm 0.25/60, kẹp đáy 0, dừng khi pause)
        if not self._legacy_stock:
            decay = FRESH_DECAY_PER_TICK
            for it in self.stock:
                it["fresh"] = max(0.0, it["fresh"] - decay)

            # Phát event spoiled {item_id, kind, location: "stock"} theo id khi fresh < 30
            spoiled_items = [it for it in self.stock if it["fresh"] < 30.0]
            if spoiled_items:
                spoiled_items.sort(key=lambda it: id_key(it["id"]))
                spoiled_ids = set()
                for it in spoiled_items:
                    spoiled_ids.add(it["id"])
                    events.append(("spoiled", {
                        "item_id": it["id"],
                        "kind": it["kind"],
                        "location": "stock",
                    }))
                # Xóa các cá thể ươn khỏi kho
                self.stock = StockList(it for it in self.stock if it["id"] not in spoiled_ids)

                # Xử lý ươn khi đang giữ chỗ:
                # Nếu cá thể đang giữ bị rơi xuống < 30, nhả toàn bộ phần giữ của đơn và thử giữ lại đúng 1 lần.
                # Nếu thiếu thì chuyển unfulfillable.
                for c in sorted(self.customers, key=lambda cust: (cust.get("order_tick", 0), id_key(cust["id"]))):
                    if c["order_status"] == "reserved":
                        res_ids = c.get("reserved_ids", [])
                        if any(iid in spoiled_ids for iid in res_ids):
                            c["reserved_ids"] = []
                            c["reserved"] = []
                            new_res = self._reserve_items_for_dish(c["dish_id"])
                            if new_res is not None:
                                c["reserved_ids"] = list(new_res)
                                c["reserved"] = list(new_res)
                            else:
                                c["order_status"] = "unfulfillable"

        # 2. Bếp nấu xong chuyển sang ready
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": s.get("order_id"),
                    "dish_id": s["dish"],
                }))

        # 3. Di chuyển và tương tác interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)

        # 4. Xử lý khách hàng (ăn xong, hết kiên nhẫn, hết ca)
        self._update_customers(events)

        # 5. Xử lý khách đặt trước (reservations)
        arrived_res = []
        for r in self.reservations:
            if r.get("arrival_tick", 0) == self.phase_tick:
                dish_id = r.get("dish_id")
                selected_ids = self._reserve_items_for_dish(dish_id) or []
                c_id = r["id"]
                cust = {
                    "id": c_id,
                    "table_id": r["table_id"],
                    "dish_id": dish_id,
                    "order_tick": self.phase_tick,
                    "state": "waiting",
                    "patience_ticks_left": int(round(self.t["patience_s"] * 60)),
                    "eat_ticks_left": 0,
                    "order_status": "reserved",
                    "reserved_ids": list(selected_ids),
                    "reserved": list(selected_ids),
                    "base_price": self.menu[dish_id]["price"] if dish_id in self.menu else 0,
                    "tip": 0,
                }
                self.customers.append(cust)
                events.append(("reservation_arrived", {
                    "id": r["id"],
                    "order_id": r["id"],
                    "table_id": r["table_id"],
                    "dish_id": dish_id,
                    "reserved": list(selected_ids),
                }))
                arrived_res.append(r["id"])
        if arrived_res:
            self.reservations = [r for r in self.reservations if r["id"] not in set(arrived_res)]

        # 6. Khách mới theo lịch
        if self.time_left_ticks > 0 and self.random_customers:
            self._spawn_customer(events)

        return events

    def _interact(self, events):
        r = self.t["interact_radius"]
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                candidates.append((d, 0, id_key(s["id"]), s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                candidates.append((d, 1, id_key(tb["id"]), tb))

        if not candidates:
            return

        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, kind, _, target = candidates[0]

        if kind == 0:
            s = target
            if s["state"] == "idle":
                # Bếp idle: lấy đơn reserved cũ nhất theo order_tick rồi đến id bàn
                reserved_orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
                if reserved_orders:
                    reserved_orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                    c = reserved_orders[0]

                    res_id_set = set(c.get("reserved_ids", []))
                    cooking_items = [it for it in self.stock if it["id"] in res_id_set]
                    self.stock = StockList(it for it in self.stock if it["id"] not in res_id_set)
                    c["reserved_ids"] = []
                    c["reserved"] = {} if self._legacy_stock else []
                    c["order_status"] = "assigned"

                    # Chốt giá món: base_price = floor(giá niêm yết * trung bình fresh của các cá thể nấu / 100)
                    listed_price = self.menu[c["dish_id"]]["price"]
                    if not self._legacy_stock:
                        if cooking_items:
                            avg_fresh = sum(it["fresh"] for it in cooking_items) / len(cooking_items)
                        else:
                            avg_fresh = 100.0
                        base_price = math.floor(listed_price * avg_fresh / 100.0)
                    else:
                        base_price = listed_price
                    c["base_price"] = base_price

                    cook_ticks = int(round(self.menu[c["dish_id"]]["cook_s"] * 60))
                    s["state"] = "cooking"
                    s["dish"] = c["dish_id"]
                    s["cook_ticks_left"] = cook_ticks
                    s["ready_ticks"] = 0
                    s["order_id"] = c["id"]
                    s["base_price"] = base_price
                    s["items"] = cooking_items

                    # Sự kiện cook_started: data.items là mảng cá thể sắp xếp theo kind rồi theo id
                    sorted_items = sorted(cooking_items, key=lambda it: (it["kind"], id_key(it["id"])))
                    items_payload = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in sorted_items]

                    events.append(("cook_started", {
                        "stove_id": s["id"],
                        "order_id": c["id"],
                        "dish_id": c["dish_id"],
                        "items": items_payload,
                        "base_price": base_price,
                    }))
            elif s["state"] == "ready":
                if self.hand is None:
                    self.hand = {
                        "order_id": s["order_id"],
                        "dish_id": s["dish"],
                        "base_price": s["base_price"],
                    }
                    events.append(("dish_picked", {
                        "stove_id": s["id"],
                        "order_id": s["order_id"],
                        "dish_id": s["dish"],
                    }))
                    s["state"] = "idle"
                    s["dish"] = None
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    s["order_id"] = None
                    s["base_price"] = 0
                    s["items"] = []
        else:
            tb = target
            cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
            if cust and cust["state"] == "waiting" and self.hand is not None and self.hand.get("order_id") == cust["id"]:
                patience_max = int(round(self.t["patience_s"] * 60))
                ratio = cust["patience_ticks_left"] / patience_max
                if "base_price" in self.hand:
                    cust["base_price"] = self.hand["base_price"]
                # Tiền boa = floor(tiền món * 0.2) trên giá đã chốt
                if ratio >= self.t["tip_min_patience_ratio"]:
                    tip = math.floor(cust["base_price"] * self.t["tip_rate"])
                else:
                    tip = 0
                cust["state"] = "eating"
                cust["order_status"] = "served"
                cust["eat_ticks_left"] = int(round(self.t["eat_s"] * 60))
                cust["tip"] = tip
                events.append(("served", {
                    "order_id": cust["id"],
                    "table_id": cust["table_id"],
                    "dish_id": cust["dish_id"],
                    "patience_ticks_left": cust["patience_ticks_left"],
                    "base_price": cust["base_price"],
                    "tip": tip,
                }))
                self.hand = None

    def _update_customers(self, events):
        by_table = sorted(self.customers, key=lambda c: id_key(c["table_id"]))

        if self.time_left_ticks > 0:
            to_remove = set()
            for c in by_table:
                if c["state"] == "eating" and c["eat_ticks_left"] <= 0:
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "finished_eating",
                    }))
                    to_remove.add(c["id"])

            for c in by_table:
                if c["id"] not in to_remove and c["state"] == "waiting" and c["patience_ticks_left"] <= 0:
                    self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer(c)
                    to_remove.add(c["id"])

            if to_remove:
                self.customers = [c for c in self.customers if c["id"] not in to_remove]
        else:
            for c in by_table:
                if c["state"] == "eating":
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "closing",
                    }))

            for c in by_table:
                if c["state"] == "waiting":
                    self._cleanup_customer(c)
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))

            self.customers = []
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))

    def _cleanup_customer(self, c):
        c["reserved_ids"] = []
        c["reserved"] = {} if self._legacy_stock else []
        for s in self.stoves:
            if s.get("order_id") == c["id"]:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                s["order_id"] = None
                s["base_price"] = 0
                s["items"] = []
        if self.hand and self.hand.get("order_id") == c["id"]:
            self.hand = None

    def _spawn_customer(self, events):
        first_tick = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * 60))
        if self.phase_tick < first_tick or (self.phase_tick - first_tick) % interval != 0:
            return

        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return

        table = free_tables[0]

        def can_cook(dish_key):
            return self._reserve_items_for_dish(dish_key) is not None

        # Mode day: bám sát theo Kế hoạch ngày (D1–D5) và tồn khả dụng
        if self.mode == "day" and self.day_plan:
            candidates = [d for d in sorted(self.planned_dishes.keys())
                          if self.planned_dishes.get(d, 0) > 0 and can_cook(d)]
            if not candidates:
                candidates = [d for d in sorted(self.day_plan.get("dishes", {}).keys())
                              if can_cook(d)]
        else:
            candidates = [d for d in sorted(self.menu.keys()) if can_cook(d)]

        if not candidates:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("customer").choice(candidates)
        if self.mode == "day" and self.planned_dishes and self.planned_dishes.get(dish_id, 0) > 0:
            self.planned_dishes[dish_id] -= 1

        selected_ids = self._reserve_items_for_dish(dish_id)
        if selected_ids is None:
            events.append(("no_dish", {}))
            return

        if self._legacy_stock:
            reserved_val = dict(self.menu[dish_id]["recipe"])
        else:
            reserved_val = list(selected_ids)

        c_id = self.ids.new("C")
        new_customer = {
            "id": c_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * 60)),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved_ids": list(selected_ids),
            "reserved": reserved_val,
            "base_price": self.menu[dish_id]["price"],
            "tip": 0,
        }
        self.customers.append(new_customer)
        events.append(("customer_arrived", {
            "order_id": c_id,
            "table_id": table["id"],
            "dish_id": dish_id,
        }))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
