"""표시 단계 기준 오차·지연 정리 (2026-10-19, iMac).

이미 측정한 자료만 다시 계산한다. 새 측정은 없다.
  - 처리 시간: 공개 저장소 tactile-vision 의 logs/metrics_2026-10-05_*.csv (7,894프레임)
  - 거리 정확도: out_distance/ground/ground_rows.csv (사진 120장, 방법별 추정 거리)
  - 구동 지연: out_latency/trials.csv (ok == 1, 17회)
  - 핀 영점: out_pin_zero/cells.csv (24칸)

모든 오차를 '핀 표시 단계'라는 같은 단위로 바꾼다. 장치 매핑은
    level = 7 * clip(ln(d_far / d) / ln(d_far / 0.5), 0, 1)        (반올림 전 연속 값)
이므로 거리 오차 d̂/d 는 7 * |ln(d̂/d)| / ln(d_far/0.5) 단계에 해당한다(d_far 안쪽).
핀 높이 오차는 한 단계 = 20 tick × 0.0646 mm = 1.292 mm 로 나눈다.

실행: python level_budget.py [--logs ~/Documents/kiro/tactile-vision/logs]
출력: out_level/summary.md, out_level/summary.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out_level"
D_NEAR = 0.5
D_FAR = {"indoor": 8.0, "outdoor": 20.0}  # 장치 ground-scale 가지 설정 (FACTS §1.9)
LEVELS = 8
MM_PER_TICK = 0.0646
MM_PER_LEVEL = 20 * MM_PER_TICK  # 1.292 mm
WALK_MPS = 1.2


def level_cont(d, d_far):
    # calib_compare.py·ground_scale.py 와 같은 식(로그 차의 비). 실내 2 m는 정확히 3.5단계 경계인데
    # 이 식은 부동소수점으로 3.4999…가 되어 단계 3이 된다 — 기존 분석([표 3])과 같은 값을 내도록 그대로 둔다.
    d = np.clip(np.asarray(d, dtype=float), D_NEAR, d_far)
    return (math.log(d_far) - np.log(d)) / (math.log(d_far) - math.log(D_NEAR)) * (LEVELS - 1)


def level_int(d, d_far):
    return np.rint(level_cont(d, d_far)).astype(int)


def stats(x):
    x = np.asarray(x, dtype=float)
    return {
        "n": int(x.size),
        "mean": float(np.mean(x)),
        "sd": float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
        "median": float(np.median(x)),
        "p95": float(np.percentile(x, 95)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
    }


def processing(logs: Path) -> dict:
    files = sorted(logs.glob("metrics_2026-10-05_*.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    out = {"files": [f.name for f in files], "frames": int(len(df))}
    for col in ["age_ms", "depth_ms", "hazard_ms", "filter_ms", "tx_ms", "total_ms"]:
        out[col] = stats(df[col])
    sc = df.loc[df["scene_ms"] > 5, "scene_ms"]  # 판별을 안 한 프레임도 0.03~0.1 ms가 기록된다
    out["scene_ms_run"] = stats(sc)
    out["scene_run_frac"] = float(len(sc) / len(df))
    out["wait_plus_total_ms"] = stats(df["age_ms"] + df["total_ms"])
    return out


def distance() -> dict:
    g = pd.read_csv(HERE / "out_distance/ground/ground_rows.csv")
    # 실내 장소 교차 더하기 보정: 다른 장소의 평균 차이(추정 − 실제)를 뺀다
    ind = g[g["env"] == "indoor"]
    b = {s: float((ind.loc[ind.site == s, "metric"] - ind.loc[ind.site == s, "true_m"]).mean())
         for s in ["site1", "site2"]}
    other = {"site1": "site2", "site2": "site1"}
    g["metric_cross"] = np.where(
        g["env"] == "indoor",
        g["metric"] - g["site"].map(lambda s: b[other[s]]),
        np.nan,
    )
    methods = {
        "indoor": ["metric", "metric_cross", "metric_b", "ground", "vkitti"],
        "outdoor": ["vkitti", "metric", "metric_b", "ground"],
    }
    res = {"indoor_offset_by_site_m": b}
    for env, ms in methods.items():
        e = g[g["env"] == env]
        dfar = D_FAR[env]
        lt = level_cont(e["true_m"], dfar)
        lti = level_int(e["true_m"], dfar)
        res[env] = {}
        for m in ms:
            est = e[m].to_numpy(float)
            ape = np.abs(est - e["true_m"].to_numpy(float)) / e["true_m"].to_numpy(float) * 100
            dl = np.abs(level_cont(est, dfar) - lt)
            li = level_int(est, dfar)
            per_site = {}
            for s in ["site1", "site2"]:
                k = (e["site"] == s).to_numpy()
                per_site[s] = {"mape": float(ape[k].mean()), "dlevel_mean": float(dl[k].mean())}
            res[env][m] = {
                "n": int(len(e)),
                "mape": float(ape.mean()),
                "dlevel_mean": float(dl.mean()),
                "dlevel_median": float(np.median(dl)),
                "dlevel_p90": float(np.percentile(dl, 90)),
                "dlevel_max": float(dl.max()),
                "level_match": float(np.mean(li == lti) * 100),
                "level_within1": float(np.mean(np.abs(li - lti) <= 1) * 100),
                "site": per_site,
            }
    return res


def latency(proc: dict) -> dict:
    t = pd.read_csv(HERE / "out_latency/trials.csv")
    t = t[t["ok"] == 1]
    res = {"n": int(len(t))}
    for col in ["onset_send_ms", "arrive_send_ms", "move_ms"]:
        res[col] = stats(t[col])
        for d in ["up", "down"]:
            res[f"{col}_{d}"] = stats(t.loc[t["dir"] == d, col])
    wp = proc["wait_plus_total_ms"]
    for key, add in [("mean", wp["mean"]), ("p95", wp["p95"]), ("max", wp["max"])]:
        on = t["onset_send_ms"] + add
        ar = t["arrive_send_ms"] + add
        res[f"total_with_{key}"] = {
            "add_ms": add,
            "onset_mean": float(on.mean()), "onset_max": float(on.max()),
            "arrive_mean": float(ar.mean()), "arrive_max": float(ar.max()),
            "meets_req": int(((on <= 500) & (ar <= 1000)).sum()),
        }
    # 박자 대기(0~200 ms 균등)의 기대값 100 ms를 뺀 나머지 = 전송·서보 응답·5 % 문턱 등
    res["onset_minus_beat_mean_ms"] = res["onset_send_ms"]["mean"] - 100.0
    # 펌웨어 속도 제한으로 계산한 5→95 % 이동 시간
    res["slew_model_move_ms"] = 140 / 4 * 5 * 0.90
    arr = res["total_with_mean"]["arrive_mean"]
    res["walk_m_at_arrive_mean"] = WALK_MPS * arr / 1000
    res["walk_m_at_arrive_max_p95"] = WALK_MPS * res["total_with_p95"]["arrive_max"] / 1000
    return res


def pin_zero() -> dict:
    c = pd.read_csv(HERE / "out_pin_zero/cells.csv")
    e = c["err_mm"].to_numpy(float)
    lv = e / MM_PER_LEVEL
    return {
        "mm": {"sd": float(np.std(e, ddof=1)), "abs_mean": float(np.abs(e).mean()),
               "abs_median": float(np.median(np.abs(e))), "min": float(e.min()), "max": float(e.max())},
        "level": {"sd": float(np.std(lv, ddof=1)), "abs_mean": float(np.abs(lv).mean()),
                  "abs_max": float(np.abs(lv).max())},
        "adjust_step_level": 5 / 20,
        "n_zero": int((e == 0).sum()), "n_gt1level": int((np.abs(c["shift_tick"]) > 20).sum()),
        "n_gt2level": int((np.abs(c["shift_tick"]) > 40).sum()),
    }


def scene_mapping() -> dict:
    out = {}
    for d in [0.5, 1, 1.5, 2, 3, 4, 6, 8]:
        li = float(level_cont(d, D_FAR["indoor"]))
        lo = float(level_cont(d, D_FAR["outdoor"]))
        out[str(d)] = {"indoor": li, "outdoor": lo, "diff": lo - li,
                       "indoor_int": int(level_int(d, D_FAR["indoor"])),
                       "outdoor_int": int(level_int(d, D_FAR["outdoor"]))}
    # 한 단계에 해당하는 거리 배율
    out["ratio_per_level"] = {k: float((v / D_NEAR) ** (1 / (LEVELS - 1))) for k, v in D_FAR.items()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=str(Path.home() / "Documents/kiro/tactile-vision/logs"))
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    proc = processing(Path(a.logs).expanduser())
    res = {
        "processing": proc,
        "distance": distance(),
        "latency": None,
        "pin_zero": pin_zero(),
        "scene_mapping": scene_mapping(),
        "mm_per_level": MM_PER_LEVEL,
    }
    res["latency"] = latency(proc)
    (OUT / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))

    L = ["# 표시 단계 기준 오차·지연 (자동 생성: level_budget.py)", ""]
    p = proc
    L.append(f"## 처리 시간 ({p['frames']}프레임, {', '.join(p['files'])})")
    for k in ["age_ms", "depth_ms", "hazard_ms", "filter_ms", "tx_ms", "total_ms", "wait_plus_total_ms"]:
        s = p[k]
        L.append(f"- {k}: 평균 {s['mean']:.1f}, SD {s['sd']:.1f}, 중앙 {s['median']:.1f}, p95 {s['p95']:.1f}, 최대 {s['max']:.1f}")
    s = p["scene_ms_run"]
    L.append(f"- scene_ms(실행 프레임 {s['n']}, {p['scene_run_frac']*100:.1f}%): 평균 {s['mean']:.1f}, SD {s['sd']:.1f}, 최대 {s['max']:.1f}")
    L.append("")
    d = res["distance"]
    L.append(f"## 거리 → 단계 오차 (실내 d_far 8 m, 실외 20 m; 실내 장소별 평균 차이 {d['indoor_offset_by_site_m']})")
    for env in ["indoor", "outdoor"]:
        for m, v in d[env].items():
            L.append(f"- {env} · {m}: MAPE {v['mape']:.1f}% (장소 {v['site']['site1']['mape']:.1f} / {v['site']['site2']['mape']:.1f}), "
                     f"|Δ단계| 평균 {v['dlevel_mean']:.2f} (중앙 {v['dlevel_median']:.2f}, p90 {v['dlevel_p90']:.2f}, 최대 {v['dlevel_max']:.2f}), "
                     f"단계 일치 {v['level_match']:.0f}%, ±1 {v['level_within1']:.0f}%")
    L.append("")
    t = res["latency"]
    L.append(f"## 구동 지연 ({t['n']}회)")
    for k in ["onset_send_ms", "arrive_send_ms", "move_ms"]:
        s = t[k]
        L.append(f"- {k}: 평균 {s['mean']:.1f}, SD {s['sd']:.1f}, 중앙 {s['median']:.1f}, 범위 {s['min']:.1f}~{s['max']:.1f}, p95 {s['p95']:.1f}")
    for k in ["total_with_mean", "total_with_p95", "total_with_max"]:
        s = t[k]
        L.append(f"- {k} (+{s['add_ms']:.1f} ms): 시작 평균 {s['onset_mean']:.1f} / 최대 {s['onset_max']:.1f}, 도착 평균 {s['arrive_mean']:.1f} / 최대 {s['arrive_max']:.1f}, 요구 만족 {s['meets_req']}/{t['n']}")
    L.append(f"- 시작 평균 − 박자 대기 기대값 100 ms = {t['onset_minus_beat_mean_ms']:.1f} ms; 속도 제한 모형 이동 시간 {t['slew_model_move_ms']:.1f} ms")
    L.append(f"- 1.2 m/s 보행 거리: 도착 평균 {t['walk_m_at_arrive_mean']:.2f} m, p95 합산 최대 {t['walk_m_at_arrive_max_p95']:.2f} m")
    L.append("")
    z = res["pin_zero"]
    L.append(f"## 핀 영점 (한 단계 {MM_PER_LEVEL:.3f} mm)")
    L.append(f"- mm: SD {z['mm']['sd']:.2f}, |e| 평균 {z['mm']['abs_mean']:.2f}, 중앙 {z['mm']['abs_median']:.2f}, 범위 {z['mm']['min']:.2f}~{z['mm']['max']:.2f}")
    L.append(f"- 단계: SD {z['level']['sd']:.2f}, |e| 평균 {z['level']['abs_mean']:.2f}, 최대 {z['level']['abs_max']:.2f}; 조정 걸음 {z['adjust_step_level']:.2f}단계")
    L.append(f"- 0칸 {z['n_zero']}, >1단계 {z['n_gt1level']}, >2단계 {z['n_gt2level']}")
    L.append("")
    L.append("## 장면별 매핑 차이 (같은 거리, 연속 단계)")
    for k, v in res["scene_mapping"].items():
        if k == "ratio_per_level":
            continue
        L.append(f"- {k} m: 실내 {v['indoor']:.2f} ({v['indoor_int']}), 실외 {v['outdoor']:.2f} ({v['outdoor_int']}), 차 {v['diff']:+.2f}")
    r = res["scene_mapping"]["ratio_per_level"]
    L.append(f"- 한 단계 거리 배율: 실내 {r['indoor']:.3f}, 실외 {r['outdoor']:.3f}")
    (OUT / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
