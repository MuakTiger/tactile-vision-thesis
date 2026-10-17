"""핀 영점 오차 — 칸별 영점 보정량을 원래 오차로 본다 (2026-10-17, 사용자 결정).

장치 쪽: ~/tactile-vision-ground/tools/pin_zero_gui.py (가지 ground-scale 커밋 439d1cb)
  사용자가 24칸을 모두 0단계(가장 먼 거리)에 두고, 칸마다 핀 윗면이 패드 표면과 같아질 때까지
  0단계 tick을 옮겼다(대부분 5 tick 걸음). 7단계 tick도 같은 양만큼 옮겨 스트로크(140 tick)는 그대로다.
  보정 전 = 24칸 공통 372 / 232 tick. 서보를 역방향으로 조립해 tick이 커지면 핀이 내려간다.
원래 오차(mm) = (보정 뒤 home − 보정 전 home) × (스트로크 mm / 스트로크 tick)
  + = 보정 전에 핀이 패드 표면 위로 나와 있었음(보정에서 내림), − = 표면 아래로 들어가 있었음.
캘리퍼스 측정은 하지 않았다. 보정 뒤 잔여 오차는 재지 않았으므로 조정 걸음(5 tick ≈ 0.32 mm)이 판단 분해능이다.

  python pin_zero.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw" / "pin_zero_20261017"
OUT = HERE / "out_pin_zero"
ROWS, COLS = 4, 6
LEVELS = 8  # 한 단계 = 스트로크 tick / 7 = 20 tick (원고 [표 1])


def load(name: str) -> dict:
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(exist_ok=True)
    before, after = load("servo_calib_before.json"), load("servo_calib_after.json")
    b = {c["ch"]: c for c in before["channels"]}
    a = {c["ch"]: c for c in after["channels"]}
    span_mm = after["_derived"]["span_mm_per_channel"]
    rows = []
    for ch in range(ROWS * COLS):
        dh = a[ch]["home_tick"] - b[ch]["home_tick"]
        dm = a[ch]["max_tick"] - b[ch]["max_tick"]
        span_t = abs(a[ch]["max_tick"] - a[ch]["home_tick"])
        mm_t = span_mm[ch] / span_t
        rows.append({"cell": ch, "row": ch // COLS + 1, "col": ch % COLS + 1, "shift_tick": dh,
                     "max_shift_tick": dm, "stroke_tick": span_t, "err_mm": round(dh * mm_t, 2)})
    assert all(r["shift_tick"] == r["max_shift_tick"] for r in rows), "home·max 이동량이 다름"
    limit = sorted({int(m.group(1)) for m in re.finditer(r"칸 (\d+) 한계",
                                                        (RAW / "pin_zero_gui_run2.log").read_text(encoding="utf-8"))})
    e = np.array([r["err_mm"] for r in rows])
    ae = np.abs(e)
    mm_t = span_mm[0] / rows[0]["stroke_tick"]
    step_t = rows[0]["stroke_tick"] / (LEVELS - 1)
    at = np.abs([r["shift_tick"] for r in rows])  # 단계 비교는 tick으로 (1단계 = 20 tick 정확히)
    st = {"n": len(e), "mean": round(float(e.mean()), 2), "sd": round(float(e.std(ddof=1)), 2),
          "abs_mean": round(float(ae.mean()), 2), "abs_median": round(float(np.median(ae)), 2),
          "min": float(e.min()), "max": float(e.max()), "mm_per_tick": round(mm_t, 4),
          "step_mm": round(step_t * mm_t, 2),
          "n_zero": int((at == 0).sum()), "n_le_1step": int((at <= step_t).sum()),
          "n_gt_1step": int((at > step_t).sum()), "n_gt_2step": int((at > 2 * step_t).sum()),
          "n_up": int((e > 0).sum()), "n_down": int((e < 0).sum()),
          "steps_max": round(float(at.max() / step_t), 1), "limit_cells": limit}
    with open(OUT / "cells.csv", "w", encoding="utf-8") as fh:
        fh.write(",".join(rows[0]) + "\n")
        for r in rows:
            fh.write(",".join(str(v) for v in r.values()) + "\n")
    grid = "\n".join("| " + " | ".join(f"{rows[r * COLS + c]['err_mm']:+.2f}" if rows[r * COLS + c]["err_mm"]
                                         else "0.00" for c in range(COLS)) + " |" for r in range(ROWS))
    lines = ["# 핀 영점 오차 (보정량 = 원래 오차, 2026-10-17)", "",
             "`python pin_zero.py` 출력. + = 보정 전 핀이 패드 표면 위로 나와 있었음.", "",
             f"- 1 tick = {st['mm_per_tick']} mm, 한 단계 = {step_t:.0f} tick = {st['step_mm']:.2f} mm",
             f"- 24칸: 평균 {st['mean']:+.2f}, 표준편차 {st['sd']:.2f}, 절댓값 평균 {st['abs_mean']:.2f}, "
             f"절댓값 중앙값 {st['abs_median']:.2f}, 범위 {st['min']:+.2f} ~ {st['max']:+.2f} mm",
             f"- 0: {st['n_zero']}칸, |오차| ≤ 1단계(0 포함): {st['n_le_1step']}칸, > 1단계: {st['n_gt_1step']}칸, "
             f"> 2단계: {st['n_gt_2step']}칸 (나옴 {st['n_up']} / 들어감 {st['n_down']}), 최대 {st['steps_max']}단계",
             f"- 조정 한계(±80 tick)에 걸린 칸: {limit or '없음'} — 그 칸의 원래 오차는 표의 값 이상일 수 있음",
             "", "칸 배치(화면과 같음, 위 줄 왼쪽부터, mm):", "",
             "| 1열 | 2열 | 3열 | 4열 | 5열 | 6열 |", "|---|---|---|---|---|---|", grid, ""]
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({"stats": st, "cells": rows}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
