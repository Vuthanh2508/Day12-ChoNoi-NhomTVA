"""Mô phỏng vòng ngày (Contract v1.1): DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> DayIntro."""

import math

from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.streams = streams
        self.ids = ids
        self.days = days

        day_scen = scenario.get("day", {})
        self.day = int(day_scen.get("day", 1))
        self.money = int(day_scen.get("money", 0))
        self.earned = int(day_scen.get("earned", 0))
        self.reputation = float(day_scen.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_scen.get("upgrades", {"oxygen": 0, "hp": 0}))
        self.active_upgrades = dict(day_scen.get("active_upgrades", self.upgrades))

        self.day_plans = list(day_scen.get("day_plan", tuning.get("day_plan", [])))
        self.day_plan = self._plan_for(self.day)

        self.phase = "gather"
        self.paused = False
        self.pause_button_down = False
        self.sim_tick = 0
        self.phase_tick = 0
        self.days_completed = 0
        self.done = False
        self.reason = None
        self._started = False

        self.shop_max_ticks = tuning.get("shop", {}).get("max_ticks", 600)
        self.stock = {}

        self.sim_gather = None
        self.sim_quan = None
        self._init_gather()

    def _plan_for(self, day):
        """Kế hoạch ngày; từ Ngày 6 trở đi lặp lại D1–D5 (Contract v1.3, soak 10 ngày)."""
        n = max((p.get("day", 0) for p in self.day_plans), default=0)
        eff = ((day - 1) % n) + 1 if n else day
        return next((p for p in self.day_plans if p.get("day") == eff),
                    {"day": day, "dishes": {}, "ingredients": {}})

    def _init_gather(self):
        g_scen = dict(self.scenario.get("gather", {}))
        g_scen.setdefault("day", self.day)  # thủy quái xuất hiện theo from_day
        g_tuning = dict(self.tuning)
        g_tuning["gather"] = dict(self.tuning["gather"])  # không sửa tuning dùng chung

        # Cấp id mới xuyên ngày theo thứ tự mảng (Contract v1.2)
        if self.day > 1 and "hold" in g_scen:
            new_hold = []
            for it in g_scen["hold"]:
                if isinstance(it, dict):
                    new_it = dict(it)
                    new_it["id"] = self.ids.new("I")
                    new_hold.append(new_it)
                else:
                    new_hold.append(it)
            g_scen["hold"] = new_hold
        elif self.day == 1 and "hold" in g_scen:
            for it in g_scen["hold"]:
                if isinstance(it, dict) and "id" in it:
                    self.ids.reserve(it["id"])

        # Áp dụng active_upgrades
        oxy_lvl = self.active_upgrades.get("oxygen", 0)
        if oxy_lvl > 0:
            upgrades_cfg = self.tuning.get("shop", {}).get("upgrades", {}).get("oxygen", [])
            for u in upgrades_cfg:
                if u["level"] == oxy_lvl:
                    g_tuning["gather"]["oxygen_max_s"] = u["oxygen_max_s"]

        hp_lvl = self.active_upgrades.get("hp", 0)
        if hp_lvl > 0:
            upgrades_cfg = self.tuning.get("shop", {}).get("upgrades", {}).get("hp", [])
            for u in upgrades_cfg:
                if u["level"] == hp_lvl:
                    g_tuning["gather"]["hp_max"] = u["hp_max"]

        self.sim_gather = GatherSim(g_tuning, g_scen, self.streams, self.ids, individual_items=True)

    def _init_quan(self, inventory):
        q_scen = dict(self.scenario.get("quan", {}))
        q_scen["day"] = self.day_plan.get("day", self.day)  # ngày hiệu lực của kế hoạch (lặp D1–D5)
        q_scen["day_plan"] = self.day_plans
        q_scen["money"] = self.money
        q_scen["earned"] = self.earned
        q_scen["reputation"] = self.reputation
        self.sim_quan = QuanSim(self.tuning, q_scen, self.streams, self.ids, inventory=inventory, mode="day")

    def _time_left_ticks(self) -> int:
        if self.phase == "gather" and self.sim_gather:
            return self.sim_gather.time_left_ticks
        elif self.phase == "quan" and self.sim_quan:
            return self.sim_quan.time_left_ticks
        elif self.phase == "shop":
            return max(0, self.shop_max_ticks - self.phase_tick)
        return 0

    @property
    def time_left_ticks(self) -> int:
        return self._time_left_ticks()

    def snapshot(self) -> dict:
        snap = {
            "day": self.day,
            "phase": self.phase,
            "day_plan": self.day_plan,
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
            "days_completed": self.days_completed,
            "sim_tick": self.sim_tick,
            "phase_tick": self.phase_tick,
            "time_left_ticks": self._time_left_ticks(),
        }
        if self.phase == "gather" and self.sim_gather:
            g_snap = self.sim_gather.snapshot()
            snap.update(g_snap)
        elif self.phase == "quan" and self.sim_quan:
            q_snap = self.sim_quan.snapshot()
            snap.update(q_snap)
            snap["shift_earned"] = self.sim_quan.shift_earned
        elif self.phase == "shop":
            snap["stock"] = ([dict(i) for i in self.stock] if isinstance(self.stock, list)
                              else dict(self.stock))

        # Đảm bảo các trường gốc của ngày không bị ghi đè bởi sub-sim
        snap["day"] = self.day
        snap["phase"] = self.phase
        snap["state"] = "paused" if self.paused else ("finished" if self.done else "playing")
        snap["sim_tick"] = self.sim_tick
        snap["phase_tick"] = self.phase_tick
        snap["active_upgrades"] = dict(self.active_upgrades)
        snap["upgrades"] = dict(self.upgrades)

        return snap

    def step(self, inp) -> list:
        events = []

        # 1. Bắn sự kiện khởi đầu ngày tại tick đầu tiên
        if not self._started:
            self._started = True
            events.append(("day_start", {}))
            events.append(("day_plan", {
                "dishes": dict(self.day_plan.get("dishes", {})),
                "ingredients": dict(self.day_plan.get("ingredients", {}))
            }))
            events.append(("phase_start", {}))

        # 2. Xử lý Pause
        if hasattr(inp, "held") and "pause" in inp.held:
            is_held = inp.held["pause"]
            if is_held != self.paused:
                self.paused = is_held
                events.append(("paused", {}) if self.paused else ("resumed", {}))
        elif inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("paused", {}) if self.paused else ("resumed", {}))

        if self.paused:
            return events

        # 3. Shortcut chuyển thẳng vào shop nếu frame có buy/shop_done khi đang ở gather
        raw_buy = getattr(inp, "raw", {}).get("buy") if hasattr(inp, "raw") else None
        if self.phase == "gather" and (raw_buy or inp.pressed("shop_done")):
            self.phase = "shop"
            self.phase_tick = 0
            events.append(("phase_start", {}))

        # 4. Gameplay theo pha
        if self.phase == "gather":
            sub_evs = self.sim_gather.step(inp)
            events.extend(sub_evs)
            self.sim_tick += 1
            self.phase_tick += 1

            if self.sim_gather.done:
                self.stock = list(self.sim_gather.inventory_items())
                # Chuyển sang quan: bàn giao trong cùng tick chuyển pha, hàng không hao thêm
                self.phase = "quan"
                self.phase_tick = 0
                self._init_quan(self.stock)
                events.append(("phase_start", {}))

        elif self.phase == "quan":
            sub_evs = self.sim_quan.step(inp)
            events.extend(sub_evs)
            self.sim_tick += 1
            self.phase_tick += 1
            self.money = self.sim_quan.money
            self.earned = self.sim_quan.earned
            self.reputation = self.sim_quan.reputation

            if self.sim_quan.done:
                self.money = self.sim_quan.money
                self.earned = self.sim_quan.earned
                self.reputation = self.sim_quan.reputation
                # Chuyển sang shop
                self.phase = "shop"
                self.phase_tick = 0
                events.append(("phase_start", {}))

        elif self.phase == "shop":
            self.sim_tick += 1
            self.phase_tick += 1

            # Xử lý lệnh buy
            buy_cmd = raw_buy or (inp.pressed("buy") if hasattr(inp, "pressed") else None)
            if buy_cmd and isinstance(buy_cmd, str):
                self._handle_buy(buy_cmd, events)

            # Xử lý đóng shop
            if inp.pressed("shop_done") or self.phase_tick >= self.shop_max_ticks:
                reason = "done" if inp.pressed("shop_done") else "time"
                events.append(("shop_end", {"reason": reason}))
                self.days_completed += 1

                if self.days_completed >= self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    # Bắt đầu ngày mới
                    self.day += 1
                    self.active_upgrades = dict(self.upgrades)
                    self.day_plan = self._plan_for(self.day)
                    self.phase = "gather"
                    self.phase_tick = 0
                    self.stock = {}
                    self._init_gather()
                    events.append(("day_start", {}))
                    events.append(("day_plan", {
                        "dishes": dict(self.day_plan.get("dishes", {})),
                        "ingredients": dict(self.day_plan.get("ingredients", {}))
                    }))
                    events.append(("phase_start", {}))

        return events

    def _handle_buy(self, upgrade_name, events):
        shop_cfg = self.tuning.get("shop", {}).get("upgrades", {})
        if upgrade_name not in shop_cfg:
            events.append(("buy_failed", {"action": upgrade_name, "reason": "unknown"}))
            return

        cur_level = self.upgrades.get(upgrade_name, 0)
        upgrades_list = shop_cfg[upgrade_name]
        next_upgrade = next((u for u in upgrades_list if u["level"] == cur_level + 1), None)
        if not next_upgrade:
            events.append(("buy_failed", {"action": upgrade_name, "reason": "max_level"}))
            return

        price = next_upgrade["price"]
        if self.money < price:
            events.append(("buy_failed", {"action": upgrade_name, "reason": "funds"}))
            return

        self.money -= price
        self.upgrades[upgrade_name] = next_upgrade["level"]
        events.append(("bought", {
            "upgrade": upgrade_name,
            "level": next_upgrade["level"],
            "price": price,
            "money": self.money
        }))
