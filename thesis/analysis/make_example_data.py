#!/usr/bin/env python3
"""
실험 1~3의 **예시 데이터** 생성기 (실측 아님).

실험을 하기 전에 논문의 표·그림·통계 틀을 완성하기 위한 값이다. 모든 CSV에 `example=1` 열이 붙는다.
실측을 하면 같은 열 이름으로 CSV를 바꾸고(example=0) `analyze.py`만 다시 돌리면 된다.

예시값을 그럴듯하게 만들기 위해 쓴 근거
  실험 1  실제 매핑 필터 코드(tactile_vision.mapping.DepthMapper)와 2026-10-05 실기 로그의 처리 시간 분포,
          Pico 펌웨어 규칙(박자 200 ms, 5 ms당 4 tick, 단계당 20 tick). 카메라 노출·전송 지연, 서보 기계 지연은 가정.
  실험 2  1 tick = 0.0646 mm(피치원 16 mm, SG90 명목 2.162 tick/도), 3D 프린팅 조립 편차는 가정.
  실험 3  전부 가정.

  python make_example_data.py            → data/exp1_latency.csv, exp2_zero_offset.csv, exp3_walking.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CODE = Path.home() / "tactile-vision" / "src"   # 장치 코드 (필터를 그대로 쓴다)
sys.path.insert(0, str(CODE))

SEED = 20261005
rng = np.random.default_rng(SEED)

# ── 장치 상수 (calib/servo_calib.json, tactile_core.h) ──
HOME_TICK, TICK_PER_LEVEL = 372, 20       # 레벨 0 = 372, 레벨 7 = 232 (역방향 조립)
MM_PER_TICK = 0.139626 / 2.1619           # 피치원 16 mm: 0.1396 mm/도, SG90 명목 2.162 tick/도
SLEW_TICK_PER_MS = 4 / 5                  # 펌웨어 5 ms마다 4 tick
BEAT_MS = 200.0


def write(name: str, rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)}행")


# ─────────────────────────────────────────────────────────
# 실험 1 — 종단 반응 시간 (사건 발생 → 핀 움직임 시작 / 목표 높이 도달)
# ─────────────────────────────────────────────────────────
def exp1() -> list[dict]:
    from tactile_vision.config import load
    from tactile_vision.mapping import DepthMapper

    cfg = load()
    rows = []
    conds = {"A_approach": (5.0, 0.5), "B_recede": (0.5, 5.0)}   # 실내, d_far 4 m. 판은 화면 가운데 4칸
    for cond, (d0, d1) in conds.items():
        for trial in range(1, 31):
            m = DepthMapper(cfg.mapping, cfg.filter, 24)
            m.set_far(4.0)
            # 사건 전 안정 상태
            for _ in range(30):
                lv0 = int(m.update(np.full(24, d0), dt=1 / 14.5)[0])
            cam_phase = rng.uniform(0, 1000 / 30)          # 카메라 프레임 위상
            cam_lat = rng.normal(42, 6)                    # 노출 중앙~USB 수신·디코드 (가정)
            mech = max(10.0, rng.normal(28, 6))            # SG90 지령→움직임 시작 지연 (가정)
            beat0 = rng.uniform(0, BEAT_MS)                # Pico 박자 위상
            # 파이프라인: 반복마다 가장 최근 프레임을 처리 (queue_size 1)
            t = rng.uniform(0, 69)
            outputs = []                                   # (출력 시각, 레벨)
            while t < 3000:
                ready = np.arange(-200, 3200, 1000 / 30) + cam_phase + cam_lat
                cap = ready[ready <= t]
                cap_t = cap[-1] - cam_lat                  # 그 프레임의 노출 시각
                dist = d1 if cap_t >= 0 else d0
                dist *= 1 + rng.normal(0, 0.03)
                proc = float(np.clip(rng.normal(68.7, 9.5), 50, 115))
                lv = int(m.update(np.full(24, dist), dt=proc / 1000)[0])
                t += proc
                outputs.append((t + 0.6, lv))              # USB 전송 0.6 ms (실측 평균)
            # Pico: 박자마다 최신 레벨 → 목표 tick, 5 ms마다 4 tick씩
            cmd, pos_hist = HOME_TICK - TICK_PER_LEVEL * lv0, []
            target = cmd
            k_out = 0
            latest = lv0
            for ms in np.arange(0, 3000, 1.0):
                while k_out < len(outputs) and outputs[k_out][0] <= ms:
                    latest = outputs[k_out][1]
                    k_out += 1
                if ms >= beat0 and (ms - beat0) % BEAT_MS < 1.0:
                    target = HOME_TICK - TICK_PER_LEVEL * latest
                if int(ms) % 5 == 0:
                    step = np.clip(target - cmd, -4, 4)
                    cmd += step
                pos_hist.append(cmd)
            pos = np.array(pos_hist, dtype=float)
            phys = np.concatenate([np.full(int(mech), pos[0]), pos])[: len(pos)]   # 기계 지연
            final = HOME_TICK - TICK_PER_LEVEL * lv  # 마지막 레벨
            moved = np.nonzero(np.abs(phys - phys[0]) * MM_PER_TICK >= 0.2)[0]
            settled = np.nonzero(np.abs(phys - final) * MM_PER_TICK <= 0.2)[0]
            settle_i = next(i for i in settled if np.all(np.abs(phys[i:] - final) * MM_PER_TICK <= 0.2))
            q = 1000 / 240                                  # 240 fps 촬영 양자화
            rows.append({
                "example": 1, "cond": cond, "trial": trial,
                "from_level": lv0, "to_level": int(lv),
                "onset_ms": round(np.ceil(moved[0] / q) * q, 1),
                "settle_ms": round(np.ceil(settle_i / q) * q, 1),
                "stroke_mm": round(abs(final - (HOME_TICK - TICK_PER_LEVEL * lv0)) * MM_PER_TICK, 2),
            })
    return rows


# ─────────────────────────────────────────────────────────
# 실험 2 — 핀 영점 편차 (레벨 0에서 패드 윗면 기준 핀 끝 높이, mm)
# ─────────────────────────────────────────────────────────
def exp2() -> list[dict]:
    rows = []
    offset = rng.normal(0.58, 0.46, 24)          # 조립 편차 (가정): 피니언 맞물림·랙 길이·서보 혼 각도
    offset[[4, 17]] += [0.95, -0.62]             # 맞물림이 한 칸 가까이 어긋난 듯한 핀 2개 (가정)
    stroke = rng.normal(8.72, 0.27, 24)          # 레벨 7까지 실제 스트로크
    corr_tick = np.rint(offset / MM_PER_TICK).astype(int)   # 보정: home tick을 핀마다 옮김
    for phase in ("before", "after"):
        for pin in range(24):
            base = offset[pin] if phase == "before" else offset[pin] - corr_tick[pin] * MM_PER_TICK + rng.normal(0, 0.07)
            for rep in range(1, 11):
                z0 = base + rng.normal(0, 0.075)         # 반복 편차 (기어 백래시·데드밴드)
                z7 = z0 + stroke[pin] + rng.normal(0, 0.09)
                rows.append({"example": 1, "phase": phase, "pin": pin, "rep": rep,
                             "zero_mm": round(z0, 2), "top_mm": round(z7, 2),
                             "home_tick": HOME_TICK + (corr_tick[pin] if phase == "after" else 0)})
    return rows


# ─────────────────────────────────────────────────────────
# 실험 3 — 실내 보행 10 m (눈가림 정상시력 8명 × 조건 3 × 배치 3)
# ─────────────────────────────────────────────────────────
def exp3() -> list[dict]:
    rows = []
    conds = ["cane", "device", "cane_device"]
    orders = [[0, 1, 2], [1, 2, 0], [2, 0, 1], [0, 2, 1], [1, 0, 2], [2, 1, 0], [0, 1, 2], [1, 2, 0]]
    base_t = {"cane": 34.0, "device": 46.5, "cane_device": 39.0}
    # 장애물 4종: low(바닥 상자 45 cm), panel(사람 크기 판), head(머리 높이 매단 판), side(벽 쪽 의자) + wall
    rate = {"cane":        {"low": 0.08, "panel": 0.30, "head": 0.85, "side": 0.12, "wall": 0.22},
            "device":      {"low": 0.45, "panel": 0.14, "head": 0.10, "side": 0.16, "wall": 0.30},
            "cane_device": {"low": 0.05, "panel": 0.09, "head": 0.12, "side": 0.06, "wall": 0.10}}
    for p in range(1, 9):
        speed = rng.normal(1.0, 0.13)                  # 개인 속도 계수
        skill = rng.normal(1.0, 0.25)                  # 개인 충돌 경향
        baseline = round(10.0 / rng.normal(1.27, 0.08), 1)   # 눈 뜨고 걷기 10 m
        for oi, ci in enumerate(orders[p - 1]):
            c = conds[ci]
            for k in range(3):                          # 시행 1~3 (배치 L1~L3, 순서 섞음)
                learn = {0: 1.0, 1: 0.90, 2: 0.84}[k] if c != "cane" else {0: 1.0, 1: 0.96, 2: 0.94}[k]
                t = base_t[c] * learn / speed * rng.lognormal(0, 0.10) + oi * -0.8
                col = {o: int(rng.poisson(r * max(0.3, skill) * (1.15 if k == 0 else 0.92))) for o, r in rate[c].items()}
                rows.append({"example": 1, "participant": f"P{p}", "cond": c, "block": oi + 1, "trial": k + 1,
                             "layout": f"L{(p + k) % 3 + 1}", "time_s": round(t, 1),
                             **{f"col_{o}": v for o, v in col.items()},
                             "baseline_s": baseline})
    return rows


if __name__ == "__main__":
    write("exp1_latency.csv", exp1())
    write("exp2_zero_offset.csv", exp2())
    write("exp3_walking.csv", exp3())
