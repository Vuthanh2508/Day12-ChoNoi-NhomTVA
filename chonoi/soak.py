"""Soak headless (Test Contract v1.3):  python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày liên tiếp trong MỘT tiến trình (gather -> quan -> shop, kế hoạch D1–D5 lặp ở Ngày 6+) bằng bot
tất định: ở Shop mua nâng cấp (oxy trước, rồi máu) và đóng shop; ở gather/quan không bấm gì.
Tiền, tổng thu, uy tín, nâng cấp, số Ngày và id cá thể chạy xuyên suốt vì dùng chung một DaySim.
soak.json: days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s.
`duration_s` là số đo thời gian thực: bỏ khi so tính lặp. Không ghi bảng xếp hạng.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .inputs import InputState
from .runner import Session

NO_MOVE = (0.0, 0.0)
MAX_TICKS_PER_DAY = 40000  # gather 10800 + quan 10800 + shop 600 + dư


def _bot_input(sim):
    """Bot tất định: chỉ hành động ở Shop."""
    if sim.phase == "shop":
        if sim.phase_tick == 1:
            return InputState(NO_MOVE, {}, set(), raw={"buy": "oxygen"})
        if sim.phase_tick == 3:
            return InputState(NO_MOVE, {}, set(), raw={"buy": "hp"})
        if sim.phase_tick == 5:
            return InputState(NO_MOVE, {}, {"shop_done"})
    return InputState(NO_MOVE, {}, set())


def run_soak(seed, days):
    tuning = load_contract()["tuning"]
    mult = tuning["score"]["reputation_multiplier"]
    sess = Session("day", tuning, {}, seed, days=days)
    results, crashes = [], 0
    t0 = time.perf_counter()
    limit = days * MAX_TICKS_PER_DAY
    while not sess.done and sess.tick < limit:
        try:
            rows = sess.step(_bot_input(sess.sim))
        except Exception:  # noqa: BLE001 - soak đếm sự cố thay vì dừng ngay
            crashes += 1
            sys.stderr.write(traceback.format_exc())
            break
        for r in rows:
            if r["name"] == "shop_end":
                sim = sess.sim
                results.append({"day": sim.days_completed, "earned": sim.earned, "reputation": sim.reputation,
                                "score": int(round(sim.earned + mult * sim.reputation))})
    return {"days": days, "days_completed": sess.sim.days_completed, "crashes": crashes,
            "results": results, "duration_s": round(time.perf_counter() - t0, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("--days phải >= 1\n")
        return 2
    result = run_soak(a.seed, a.days)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["crashes"] == 0 and result["days_completed"] == a.days else 1


if __name__ == "__main__":
    sys.exit(main())
