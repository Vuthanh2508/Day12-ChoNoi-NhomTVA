"""Benchmark có render (Test Contract v1.3):  python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng (gather) seed đã cho, Út Sen đứng yên ở bến, cá bơi, Cá Sấu, hiệu ứng mặc định, 1280x720.
Làm nóng 3 s rồi đo `--duration` giây. Cách đo: mở client (`chonoi/web/index.html`) trong Edge/Chrome headless;
client ghi thời gian từng khung (requestAnimationFrame) rồi gửi về /bench. Không có trình duyệt -> đo dự phòng
chỉ phần mô phỏng + snapshot (không có vẽ), in cảnh báo ra stderr.
Xuất đúng 5 trường: avg_fps, p1_low_fps, frames, measured_s, load_ms.
"""

import argparse
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import time

from .contract import load_contract
from .inputs import LiveInputs
from .live import LiveGame, LiveServer
from .runner import Session

WARMUP_S = 3.0


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env and os.path.exists(env):
        return env
    for name in ("microsoft-edge", "msedge", "google-chrome", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if os.path.exists(p):
            return p
    return None


def metrics(deltas_ms, load_ms):
    """deltas_ms: thời gian mỗi khung (ms) trong khoảng đo."""
    d = [x / 1000.0 for x in deltas_ms if x > 0]
    frames = len(d)
    measured = sum(d)
    if frames == 0 or measured <= 0:
        return {"avg_fps": 0, "p1_low_fps": 0, "frames": 0, "measured_s": 0, "load_ms": int(load_ms)}
    k = max(1, math.ceil(0.01 * frames))
    slow = sorted(d, reverse=True)[:k]
    return {"avg_fps": round(frames / measured, 2), "p1_low_fps": round(1.0 / (sum(slow) / k), 2),
            "frames": frames, "measured_s": round(measured, 3), "load_ms": int(round(load_ms))}


def bench_browser(browser, game, duration):
    srv = LiveServer(game, port=0)
    srv.start()
    prof = tempfile.mkdtemp(prefix="chonoi-bench-")
    t_launch = time.perf_counter()
    url = f"{srv.url}?bench=1&duration={duration}&warmup={WARMUP_S}"
    proc = subprocess.Popen([browser, "--headless=new", "--window-size=1280,720", "--no-first-run",
                             "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                             "--disable-backgrounding-occluded-windows", f"--user-data-dir={prof}", url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        load_ms = None
        deadline = time.perf_counter() + 60 + WARMUP_S + duration
        while time.perf_counter() < deadline:
            try:
                ev = game.bench_events.get(timeout=0.5)
            except queue.Empty:
                continue
            if ev["event"] == "first_frame" and load_ms is None:
                load_ms = (time.perf_counter() - t_launch) * 1000
            elif ev["event"] == "done":
                return metrics(ev.get("deltas", []), load_ms or 0)
        raise RuntimeError("hết giờ chờ trình duyệt báo kết quả")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        srv.stop()
        shutil.rmtree(prof, ignore_errors=True)


def bench_fallback(tuning, seed, duration):
    """Không có trình duyệt: đo bước mô phỏng + tạo snapshot JSON mỗi 'khung' (không có vẽ)."""
    t0 = time.perf_counter()
    sess = Session("gather", tuning, {}, seed)
    inputs = LiveInputs()
    load_ms = (time.perf_counter() - t0) * 1000
    for _ in range(int(WARMUP_S * 60)):
        sess.step(inputs.advance())
    deltas, end = [], time.perf_counter() + duration
    while time.perf_counter() < end and not sess.done:
        t = time.perf_counter()
        sess.step(inputs.advance())
        json.dumps(sess.snapshot())
        deltas.append((time.perf_counter() - t) * 1000)
    return metrics(deltas, load_ms)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("--duration phải > 0\n")
        return 2
    tuning = load_contract()["tuning"]
    browser = find_browser()
    try:
        if browser:
            game = LiveGame("gather", tuning, {}, a.seed)
            result = bench_browser(browser, game, a.duration)
        else:
            sys.stderr.write("cảnh báo: không tìm thấy Edge/Chrome (đặt CHONOI_BROWSER); đo dự phòng không có vẽ\n")
            result = bench_fallback(tuning, a.seed, a.duration)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"bench lỗi: {e}\n")
        return 1
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
