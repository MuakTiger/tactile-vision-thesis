"""보정 방법 비교와 땅 거리 비 (2026-10-17 젯슨 세션에서 탐색한 계산을 정식 저장).

1. 보정 5가지(곱하기·더하기·1차식·거듭제곱·이론 k) × 장소 교차(한 장소로 맞춘 식을 다른 장소에 적용).
   지표: MAPE, 가까운 거리(실내 ≤ 1 m, 실외 ≤ 2 m) MAPE, 핀 단계 일치·±1단계(장치 log 매핑, 필터 없음).
2. 땅 거리 비: 화면 아래 땅 줄(1.82~3.5 m, 렌즈 높이 0.70 m·수평 가정)에서 모델 깊이 / 기하 깊이.
   실외 모델(VKITTI2) 이론 배율 = (1.65 / 0.70) × (725 / 375) / (908 / 698) ≈ 3.50
   (KITTI 카메라 높이 1.65 m·초점 725 px·세로 375 px 가정 대 장치 0.70 m·908 px·698 px).

  python calib_compare.py      # exp_distance.csv와 depth_cache 필요 (CPU)
"""
from __future__ import annotations

import csv
import io
import math
import sys
from contextlib import redirect_stdout

import numpy as np

from distance_analysis import OUT_CSV, OUT_DIR, SITES
from relative_depth import CACHE, CY_RAW, F_RAW, GROUND_MAX_M, H_CAM

rows = [r for r in csv.DictReader(open(OUT_CSV, encoding="utf-8")) if r["method"] == "roi"]
K_TH = (0.70 * 908 / 698) / (1.65 * 725 / 375)
FAR = {"indoor": 8.0, "outdoor": 20.0}  # 장치 ground-scale 가지 d_far (2026-10-17 사용자 결정, 이전 4 / 8 m)


def level(d, far):  # 장치 log 매핑(near 0.5, 8단계), 필터 없이
    d = np.clip(d, 0.5, far)
    return np.rint((math.log(far) - np.log(d)) / (math.log(far) - math.log(0.5)) * 7).astype(int)


def calib_table():
    fits = {
        '보정 없음':        (lambda t, e: None,                                   lambda p, e: e),
        '곱하기 k':         (lambda t, e: np.sum(t*e)/np.sum(e*e),               lambda p, e: p*e),
        '더하기 b':         (lambda t, e: np.mean(t-e),                           lambda p, e: e+p),
        '1차식 a·e+b':      (lambda t, e: np.polyfit(e, t, 1),                    lambda p, e: np.polyval(p, e)),
        '거듭제곱 c·e^p':   (lambda t, e: np.polyfit(np.log(e), np.log(t), 1),    lambda p, e: np.exp(np.polyval(p, np.log(e)))),
        '이론 k 0.285':     (lambda t, e: None,                                   lambda p, e: K_TH*e),
    }
    for env in ('indoor', 'outdoor'):
        far = FAR[env]
        for model in (env, 'outdoor' if env == 'indoor' else 'indoor'):
            print(f"\n== {'실내' if env=='indoor' else '실외'} 사진 × {'실내' if model=='indoor' else '실외'} 모델"
                  f"{' (주)' if env==model else ' (보조)'}  — 장소 교차, d_far {far:g} m")
            data = {s: [r for r in rows if r['env']==env and r['model']==model and r['site']==s] for s in ('site1','site2')}
            for name, (fit, apply) in fits.items():
                if name.startswith('이론') and model != 'outdoor': continue
                ape, near_ape, lv_ok, lv_1 = [], [], [], []
                for a, b in (('site1','site2'), ('site2','site1')):
                    ta = np.array([float(r['true_m']) for r in data[a]]); ea = np.array([float(r['est_m']) for r in data[a]])
                    tb = np.array([float(r['true_m']) for r in data[b]]); eb = np.array([float(r['est_m']) for r in data[b]])
                    p = fit(ta, ea)
                    pb = np.maximum(apply(p, eb), 0.05)
                    ape += list(np.abs(pb-tb)/tb*100)
                    near = tb <= (1.0 if env=='indoor' else 2.0)
                    near_ape += list((np.abs(pb-tb)/tb*100)[near])
                    dl = level(pb, far) - level(tb, far)
                    lv_ok += list(dl == 0); lv_1 += list(np.abs(dl) <= 1)
                print(f"  {name:14s} MAPE {np.mean(ape):6.1f}%  가까운 거리 {np.mean(near_ape):6.1f}%  "
                      f"단계 일치 {np.mean(lv_ok)*100:3.0f}%  ±1단계 {np.mean(lv_1)*100:3.0f}%")


def ground_ratio():
    """사진마다 땅 줄의 (모델 깊이 / 기하 깊이) 중앙값 → 장소별 중앙값과 범위."""
    print("\n== 땅 거리 비 (모델 깊이 / 기하 깊이, 땅 줄 1.82~3.5 m, 모든 열)")
    for folder in SITES:
        rat = {"indoor": [], "outdoor": []}
        for p in sorted((CACHE / folder).glob("*.npz")):
            z = np.load(p)
            _, cy, _, ch = (int(v) for v in z["crop"])
            H = z["indoor_depth_m"].shape[0]
            f = F_RAW * H / ch
            y0 = (CY_RAW - cy) * H / ch
            ys = np.arange(int(math.ceil(y0 + f * H_CAM / GROUND_MAX_M)), H)
            zg = f * H_CAM / (ys - y0)
            for k in rat:
                med = np.median(z[f"{k}_depth_m"][ys], axis=1)
                rat[k].append(float(np.median(med / zg)))
        print(f"  {folder:14s} " + "  ".join(
            f"{k} 모델 {np.median(v):.2f} ({min(v):.2f}~{max(v):.2f})" for k, v in rat.items()))
    print(f"  실외 모델 이론 배율 {1 / K_TH:.2f}")


def main() -> int:
    buf = io.StringIO()
    with redirect_stdout(buf):
        calib_table()
        ground_ratio()
    text = buf.getvalue()
    (OUT_DIR / "calib_compare.md").write_text("# 보정 방법 비교와 땅 거리 비 (자동 생성: `calib_compare.py`)\n```\n"
                                              + text.strip() + "\n```\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
