"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, individual_items=False):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        # Phase 3: every collected item has its own ID and freshness.
        self.hold = []
        for raw in scenario.get("hold", []):
            if isinstance(raw, dict):
                item = {
                    "id": str(raw["id"]),
                    "kind": raw["kind"],
                    "fresh": float(raw["fresh"]),
                }
                ids.reserve(item["id"])
            else:
                # Compatibility with direct Phase 1/2 test fixtures.
                item = {
                    "id": ids.new("I"),
                    "kind": raw,
                    "fresh": 100.0,
                }
            self.hold.append(item)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.tick = int(scenario.get("tick", 0))
        self.paused = bool(scenario.get("paused", False))
        # Phase 3: deterministic flood-current state.
        self.current_direction = 0
        current_cfg = t["current"]
        interval = int(current_cfg["interval_ticks"])
        duration = int(current_cfg["duration_ticks"])
        if interval <= 0 or duration <= 0 or duration >= interval:
            raise ValueError("Invalid current timing configuration")
        self.forced_current_direction = scenario.get("current_direction")
        current_rng = self.rng.get("current")
        for _ in range(self.tick // interval):
            self.current_direction = current_rng.choice((-1, 1))
        if self.tick < interval or self.tick % interval >= duration:
            self.current_direction = 0
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # Fish initialization: support Phase 1 and Phase 2 contracts
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif not scenario.get("random_fish", True):
            src_fish = []
        elif isinstance(t["fish_initial"], list):
            src_fish = t["fish_initial"]
        else:
            # Preserve Phase 1 fixtures for regression compatibility
            src_fish = [
                {"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                {"id": "F2", "kind": "ca_loc", "pos": [30, 10]},
                {"id": "F3", "kind": "ca_linh", "pos": [45, 10]},
                {"id": "F4", "kind": "ca_loc", "pos": [60, 16]},
                {"id": "F5", "kind": "ca_linh", "pos": [75, 5]},
                {"id": "F6", "kind": "ca_loc", "pos": [90, 16]},
            ]

            rng = self.rng.get("fish_spawn")
            kinds = list(t["fish_weights"])
            weights = [t["fish_weights"][k] for k in kinds]

            for number in range(
                len(src_fish) + 1,
                int(t["fish_initial"]) + 1
            ):
                if hasattr(rng, "choices"):
                    kind = rng.choices(kinds, weights=weights, k=1)[0]
                else:
                    r = rng.random()
                    total = sum(weights)
                    acc = 0.0
                    kind = kinds[-1]
                    for k, w in zip(kinds, weights):
                        acc += w / total
                        if r < acc:
                            kind = k
                            break
                x = rng.choice(t["fish_spawn_x"])
                d = rng.choice(t["fish_spawn_depths"][kind])

                src_fish.append({
                    "id": f"F{number}",
                    "kind": kind,
                    "pos": [x, d],
                    "heading_deg": rng.choice([0, 180])
                })

        self.fish = [
            {
                "id": f["id"],
                "kind": f["kind"],
                "pos": [float(c) for c in f["pos"]],
                "heading_deg": float(f.get("heading_deg", 0))
            }
            for f in src_fish
        ]

        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None
        # Phase 2 monsters. Scenario can override with [] for isolated tests.
        self.day = int(scenario.get("day", scenario.get("day_number", 1)))
        self.monsters = []
        for source in scenario.get("monsters", t["monsters"]["spawns"]):
            if self.day < int(source.get("from_day", 1)):
                continue
            waypoints = [[float(v) for v in pt] for pt in source["waypoints"]]
            monster = {
                "id": source["id"], "kind": source["kind"],
                "pos": [float(v) for v in source["pos"]],
                "waypoints": waypoints,
                "target_index": int(source.get("target_index", 1)),
                "state": source.get("state", "patrol"),
                "recoil_ticks": int(source.get("recoil_ticks", 0)),
                "recoil_dir": list(source.get("recoil_dir", [1.0, 0.0])),
            }
            self.monsters.append(monster)
            ids.reserve(monster["id"])

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        """Contract v1.2: preserve individual item IDs and freshness."""
        return [dict(item) for item in sort_by_id(self.hold)]
    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "current": self._current_snapshot(),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
             "monsters": [{"id": m["id"], "kind": m["kind"],
                           "pos": list(m["pos"]), "state": m["state"],
                           "recoil_ticks": m["recoil_ticks"]}
                          for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []

        # Phase 3: pause freezes all simulation timers and freshness.
        if inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("paused" if self.paused else "resumed", {}))
            return events

        if self.paused or self.done:
            return events
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # Phase 2: update fish before player interaction
        self.tick += 1
        self._update_current(events)
        self._update_freshness(events)
        self._update_fish(events)

        # 2. Movement, oxygen and drowning
        was_surface = self._at_surface()
        self._move(inp)
        if self.current_direction and self.pos[1] >= float(self.t["current"]["min_depth"]):
            lo, hi = self.t["bounds"]["x"]
            self.pos[0] = max(lo, min(hi, self.pos[0] + self.current_direction
                                      * float(self.t["current"]["speed"]) / TICK))
        at_surface = self._at_surface()

        if was_surface and not at_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and at_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        old_oxygen = self.oxygen_ticks

        if at_surface:
            self.oxygen_ticks = min(
                self.oxygen_max,
                self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"])
            )
            self.zero_oxy_ticks = 0
        else:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)

            if old_oxygen > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))

            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1

                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)

                    events.append(("choke", {"hp": self.hp}))

                    if self.hp == 0:
                        lost = list(reversed(self.hold))
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events
            else:
                self.zero_oxy_ticks = 0

        # Phase 2: update monsters after player movement/oxygen, before actions.
        self._update_monsters(events)
        if self.done:
            return events

        # 3. Interact: dock first, then gather
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events

            if at_surface:
                candidates = [
                    n for n in self.nodes
                    if n["regrow_ticks"] == 0
                    and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]
                ]

                if candidates:
                    node = min(
                        sort_by_id(candidates),
                        key=lambda n: math.dist(self.pos, n["pos"])
                    )
                    quantity = int(self.t["node_yield"])
                    free = max(0, self.t["hold_capacity"] - len(self.hold))

                    if len(self.hold) + quantity > self.t["hold_capacity"]:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": node["id"],
                            "required": quantity,
                            "free": free,
                        }))
                    else:
                        self.hold.extend(self._new_items(node["kind"], quantity))
                        node["regrow_ticks"] = int(
                            round(self.t["regrow_s"] * TICK)
                        )
                        events.append((
                            "gather",
                            {
                                "node_id": node["id"],
                                "kind": node["kind"],
                                "amount": quantity
                            }
                        ))

        # 4. Catch fish underwater
        if (
            inp.pressed("catch")
            and not at_surface
            and self.catch_cd_ticks == 0
        ):
            candidates = [
                f for f in self.fish
                if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]
            ]

            if candidates:
                fish = min(
                    sort_by_id(candidates),
                    key=lambda f: math.dist(self.pos, f["pos"])
                )
                quantity = int(self.t["fish_yield"][fish["kind"]])
                free = max(0, self.t["hold_capacity"] - len(self.hold))

                if len(self.hold) + quantity > self.t["hold_capacity"]:
                    events.append(("hold_full", {
                        "action": "catch",
                        "fish_id": fish["id"],
                        "required": quantity,
                        "free": free,
                    }))
                else:
                    self.hold.extend(self._new_items(fish["kind"], quantity))
                    self.fish.remove(fish)
                    self.catch_cd_ticks = int(
                        round(self.t["catch_cooldown_s"] * TICK)
                    )

                    events.append((
                        "fish_caught",
                        {
                            "fish_id": fish["id"],
                            "kind": fish["kind"],
                            "yield": quantity
                        }
                    ))

        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- Phase 3: individual items and freshness -------------------------------
    def _new_items(self, kind, quantity):
        return [
            {
                "id": self.ids.new("I"),
                "kind": kind,
                "fresh": 100.0,
            }
            for _ in range(quantity)
        ]

    def _current_snapshot(self):
        if not self.current_direction:
            return None
        duration = int(self.t["current"]["duration_ticks"])
        left = duration - self.tick % int(self.t["current"]["interval_ticks"])
        return {"direction": self.current_direction, "ticks_left": left}

    def _update_current(self, events):
        """Scheduled current warning/start/end at exact simulation ticks."""
        cfg = self.t["current"]
        interval = int(cfg["interval_ticks"])
        duration = int(cfg["duration_ticks"])
        warning = int(cfg["warning_ticks"])
        phase = self.tick % interval

        if self.tick >= interval and phase == 0:
            forced = self.forced_current_direction
            self.current_direction = forced if forced else self.rng.get("current").choice((-1, 1))
            events.append(("current_start", {
                "direction": self.current_direction,
            }))

        elif self.tick >= interval and phase == duration:
            old_direction = self.current_direction
            self.current_direction = 0
            events.append(("current_end", {
                "direction": old_direction,
            }))

        elif phase == interval - warning:
            events.append(("current_warning", {
                "start_tick": self.tick + warning,
            }))

    def _update_freshness(self, events):
        decay = 0.5 / TICK
        for item in self.hold:
            before = float(item["fresh"])
            after = max(0.0, before - decay)
            item["fresh"] = after

            # Compare raw floating-point values, before display rounding.
            if before >= 30.0 and after < 30.0:
                events.append(("spoiled", {
                    "item_id": item["id"],
                    "kind": item["kind"],
                    "location": "hold",
                }))

    # --- Phase 2: fish simulation ----------------------------------------------
    def _update_fish(self, events):
        """Move fish at 60 Hz, turn every 120 ticks, spawn every 360."""
        t = self.t
        rng = self.rng.get("fish_movement")
        speed = float(t["fish_speed"])
        x_min, x_max = map(float, t["fish_x"])
        turn_ticks = int(t["fish_turn_ticks"])

        for fish in sort_by_id(self.fish):
            kind = fish["kind"]
            depth_min, depth_max = map(
                float, t["fish_depths"][kind]
            )

            # Deterministic direction change on exact tick boundaries.
            if turn_ticks > 0 and self.tick % turn_ticks == 0:
                options = [0.0, 90.0, 180.0, 270.0]
                old = float(fish["heading_deg"]) % 360.0
                choices = [h for h in options if h != old]
                fish["heading_deg"] = rng.choice(choices)

            angle = math.radians(fish["heading_deg"])
            dx = math.cos(angle) * speed / TICK
            dd = math.sin(angle) * speed / TICK

            new_x = fish["pos"][0] + dx
            new_d = fish["pos"][1] + dd

            # Reflect rather than leave the allowed area.
            if new_x < x_min or new_x > x_max:
                new_x = (
                    2 * x_min - new_x if new_x < x_min
                    else 2 * x_max - new_x
                )
                fish["heading_deg"] = (
                    180.0 - fish["heading_deg"]
                ) % 360.0

            if new_d < depth_min or new_d > depth_max:
                new_d = (
                    2 * depth_min - new_d if new_d < depth_min
                    else 2 * depth_max - new_d
                )
                fish["heading_deg"] = (
                    -fish["heading_deg"]
                ) % 360.0

            fish["pos"] = [
                max(x_min, min(x_max, new_x)),
                max(depth_min, min(depth_max, new_d)),
            ]

        spawn_ticks = int(t["fish_spawn_ticks"])
        if spawn_ticks > 0 and self.tick % spawn_ticks == 0:
            self._spawn_fish(events)

    def _spawn_fish(self, events):
        """Spawn one school, respecting population and clearance."""
        t = self.t
        if len(self.fish) >= int(t["fish_max"]):
            return

        rng = self.rng.get("fish_spawn")
        kinds = list(t["fish_weights"])
        weights = [float(t["fish_weights"][k]) for k in kinds]

        if hasattr(rng, "choices"):
            kind = rng.choices(kinds, weights=weights, k=1)[0]
        else:
            r = rng.random()
            total = sum(weights)
            acc = 0.0
            kind = kinds[-1]
            for k, w in zip(kinds, weights):
                acc += w / total
                if r < acc:
                    kind = k
                    break
        depths = t["fish_spawn_depths"][kind]
        clearance = float(t["fish_spawn_clearance"])

        # Pick a valid spawn location with deterministic retries.
        for _ in range(100):
            pos = [
                float(rng.choice(t["fish_spawn_x"])),
                float(rng.choice(depths)),
            ]

            if all(
                math.dist(pos, other["pos"]) >= clearance
                for other in self.fish
            ):
                fish = {
                    "id": self.ids.new("F"),
                    "kind": kind,
                    "pos": pos,
                    "heading_deg": float(rng.choice([0, 180])),
                }
                self.fish.append(fish)
                events.append(("fish_spawned", {
                    "fish_id": fish["id"],
                    "kind": fish["kind"],
                    "pos": list(pos),
                }))
                return

        # No valid location found: skip this spawn interval.

    # --- Phase 2: monsters ------------------------------------------------------
    @staticmethod
    def _approach(origin, target, distance):
        dx, dd = target[0] - origin[0], target[1] - origin[1]
        length = math.hypot(dx, dd)
        if length <= 1e-12:
            return list(origin), True
        ratio = min(1.0, distance / length)
        return [origin[0] + dx * ratio, origin[1] + dd * ratio], ratio >= 1.0

    def _update_monsters(self, events):
        cfg = self.t["monsters"]
        for monster in sort_by_id(self.monsters):
            kind = monster["kind"]
            spec = cfg["species"][kind]

            if monster["recoil_ticks"] > 0:
                step = float(spec["recoil_dist"]) / float(spec["recoil_ticks"])
                direction = monster["recoil_dir"]
                monster["pos"][0] += direction[0] * step
                monster["pos"][1] += direction[1] * step
                self._clamp_monster(monster)
                monster["recoil_ticks"] -= 1
                if monster["recoil_ticks"] == 0:
                    monster["state"] = "patrol"
                continue  # No attack during recoil.

            dist = math.dist(monster["pos"], self.pos)
            depth_lo, depth_hi = spec["depths"]
            depth_ok = depth_lo <= self.pos[1] <= depth_hi
            if monster["state"] == "chase":
                if not depth_ok or dist > float(spec["exit_radius"]):
                    monster["state"] = "patrol"
                    events.append(("monster_patrol", {"monster_id": monster["id"]}))
            elif depth_ok and dist <= float(spec["detect_radius"]) and self.invuln_ticks == 0:
                monster["state"] = "chase"
                events.append(("monster_chase", {"monster_id": monster["id"]}))

            if monster["state"] == "chase":
                monster["pos"], _ = self._approach(
                    monster["pos"], self.pos, float(spec["chase_speed"]) / TICK
                )
            else:
                target = monster["waypoints"][monster["target_index"]]
                monster["pos"], arrived = self._approach(
                    monster["pos"], target, float(spec["patrol_speed"]) / TICK
                )
                if arrived:
                    monster["target_index"] = (
                        monster["target_index"] + 1
                    ) % len(monster["waypoints"])
            self._clamp_monster(monster)

            if (math.dist(monster["pos"], self.pos) <= float(spec["hit_radius"])
                    and self.invuln_ticks == 0):
                self.hp = max(0, self.hp - 1)
                count = int(len(self.hold) * float(cfg["loss_ratio"]))
                lost = list(reversed(self.hold[-count:])) if count else []
                if count:
                    del self.hold[-count:]
                events.append(("monster_hit", {
                    "monster_id": monster["id"], "kind": kind,
                    "hp": self.hp, "lost": lost,
                }))
                self.invuln_ticks = int(cfg["invuln_ticks"])
                monster["state"] = "recoil"
                monster["recoil_ticks"] = int(spec["recoil_ticks"])
                dx = monster["pos"][0] - self.pos[0]
                dd = monster["pos"][1] - self.pos[1]
                norm = math.hypot(dx, dd)
                monster["recoil_dir"] = (
                    [dx / norm, dd / norm] if norm > 1e-12 else [1.0, 0.0]
                )
                if self.hp == 0:
                    rest = list(reversed(self.hold))
                    self.hold.clear()
                    events.append(("faint", {
                        "cause": "monster", "monster_id": monster["id"],
                        "hp": 0, "lost": lost + rest,
                    }))
                    self._finish("fainted", events)
                    return

    def _clamp_monster(self, monster):
        bounds = self.t["bounds"]
        for index, axis in enumerate(AXES):
            lo, hi = bounds[axis]
            monster["pos"][index] = max(float(lo), min(float(hi), monster["pos"][index]))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            # Current adds to horizontal displacement, not swimming velocity.
            displacement_speed = self.vel[i]
            self.pos[i] += displacement_speed / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
