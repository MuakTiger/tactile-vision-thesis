"""땅 기준 거리 환산 검증 — 상대 깊이를 카메라 높이·화각으로 m로 바꾸는 방법.

방법 (장치에서 돌릴 방식 그대로, 상자 위치는 쓰지 않음):
  1. 상대 깊이 모델(Depth Anything V2 ViT-S, metric 미세조정 전) → 상대 역깊이 r (클수록 가까움)
  2. 카메라 높이 h, 수평, 초점거리 f이면 화면 y줄의 땅까지 앞쪽 거리 d(y) = f·h / (y − y0)
     (y0 = 수평선 줄. 장치 입력의 맨 아래 줄이 약 1.82 m)
  3. 땅으로 보는 줄(1.82~3.5 m)마다 r 중앙값 × d(y) → 그 중앙값 A.
     r = A / d 로 본다(하늘 r ≈ 0이므로 이동 0 가정)
  4. 거리 = A / r
상자 거리로 맞춘 값이 하나도 없으므로 사진 120장 전체가 검증 자료다.
비교: 실내 metric 모델 − 0.44 m(실내 사진으로 정한 값이라 실외 사진에는 독립), 보정 없는 두 metric 모델.

  python ground_scale.py     # relative_depth.py --build 로 만든 캐시가 필요 (CPU만 씀)
"""
from __future__ import annotations

import csv
import json
import math
import sys

import numpy as np
from scipy import stats

from distance_analysis import OUT_CSV, OUT_DIR, inner_slice, load_rois, load_shots, roi_to_model, setup_mpl
from relative_depth import B_INDOOR, CACHE, CY_RAW, F_RAW, GROUND_MAX_M, H_CAM, NEAR

OUT = OUT_DIR / "ground"
FAR = 8.0                 # 핀 단계 비교용 d_far
SITE_KO = {"site1": "장소 1", "site2": "장소 2"}
PLACE = {("outdoor", "site1"): "실외 1 산책로", ("outdoor", "site2"): "실외 2 주차장",
         ("indoor", "site1"): "실내 1 거실", ("indoor", "site2"): "실내 2 주방"}
METHODS = {"ground": "땅 기준 상대 깊이", "metric_b": "실내 모델 - 0.44 m",
           "metric": "실내 모델 (보정 없음)", "vkitti": "실외 모델 (보정 없음)"}
COLOR = {"ground": "#1b9e77", "metric_b": "#2a78d6"}
N_BOOT = 10000


def level(d: float, far: float = FAR) -> int:
    if not math.isfinite(d) or d >= far:
        return 0
    if d <= NEAR:
        return 7
    return int(np.rint(7 * (math.log(far) - math.log(d)) / (math.log(far) - math.log(NEAR))))


def scale_A(rel: np.ndarray, crop, h=H_CAM, tilt_deg=0.0, f_mul=1.0, gmax=GROUND_MAX_M) -> float:
    """땅 줄에서 A를 구한다. tilt_deg > 0 = 카메라가 실제로는 그만큼 아래를 보는데 수평으로 가정한 경우."""
    H = rel.shape[0]
    _, cy, _, ch = crop
    f = F_RAW * f_mul * H / ch
    y0 = (CY_RAW - cy) * H / ch + F_RAW * H / ch * math.tan(math.radians(tilt_deg))
    vals = []
    for r in range(int(math.ceil(y0 + f * h / gmax)), H):
        vals.append(float(np.median(rel[r])) * f * h / (r - y0))
    return float(np.median(vals))


def collect() -> tuple[list[dict], dict]:
    rois = load_rois()
    other = {}
    with OUT_CSV.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            other[(r["site"], r["file"], r["model"])] = float(r["est_m"])
    rows, cache = [], {}
    for s in load_shots():
        key = (s["folder"], s["file"])
        if key not in rois:
            continue
        p = CACHE / s["folder"] / s["file"].replace(".png", ".npz")
        crop = tuple(int(v) for v in np.load(p)["crop"])
        rel = np.load(p.with_name(p.stem + "_rel.npy")).astype(np.float32)
        rs, cs = inner_slice(roi_to_model(rois[key], crop, (rel.shape[1], rel.shape[0])),
                             (rel.shape[1], rel.shape[0]))
        r_box = float(np.median(rel[rs, cs]))
        A = scale_A(rel, crop)
        m = other[(s["site"], s["file"], "indoor")]
        rows.append({"env": s["env"], "site": s["site"], "file": s["file"], "true_m": s["true_m"],
                     "r_box": r_box, "A": A, "ground": A / r_box if r_box > 0 else float("inf"),
                     "metric_b": m + B_INDOOR, "metric": m, "vkitti": other[(s["site"], s["file"], "outdoor")]})
        if s["env"] == "outdoor":
            cache[s["file"]] = (rel, crop, r_box)
    return rows, cache


def ape(r: dict, k: str) -> float:
    return abs(r[k] - r["true_m"]) / r["true_m"] * 100


def block(rs: list[dict], k: str) -> dict:
    a = np.array([ape(r, k) for r in rs])
    lv = np.array([level(r[k]) - level(r["true_m"]) for r in rs])
    return {"n": len(rs), "mape": float(a.mean()), "median_ape": float(np.median(a)),
            "step_exact": float(np.mean(lv == 0) * 100), "step_pm1": float(np.mean(np.abs(lv) <= 1) * 100)}


def clusters(rs: list[dict], k: str) -> dict:
    """장소×거리 묶음(사진 5장)마다 평균 APE. 같은 장면을 연달아 찍은 5장은 독립이 아니므로 묶음을 단위로 본다."""
    out = {}
    for r in rs:
        out.setdefault((r["site"], r["true_m"]), []).append(ape(r, k))
    return {c: float(np.mean(v)) for c, v in out.items()}


def compare(rs: list[dict], a: str, b: str) -> dict:
    """a − b. 사진 단위 윌콕슨(참고), 묶음 단위 윌콕슨(정확), 묶음 부트스트랩 95% 구간."""
    pa, pb = np.array([ape(r, a) for r in rs]), np.array([ape(r, b) for r in rs])
    ca, cb = clusters(rs, a), clusters(rs, b)
    keys = sorted(ca)
    da = np.array([ca[c] for c in keys]) - np.array([cb[c] for c in keys])
    rng = np.random.default_rng(0)
    boot = np.array([da[rng.integers(0, len(da), len(da))].mean() for _ in range(N_BOOT)])
    return {"photo_n": len(pa), "photo_wilcoxon_p": float(stats.wilcoxon(pa, pb).pvalue),
            "cluster_n": len(keys), "cluster_wins": int(np.sum(da < 0)),
            "cluster_wilcoxon_p": float(stats.wilcoxon(da, method="exact").pvalue),
            "mape_diff": float(da.mean()), "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}


def sensitivity(rows: list[dict], cache: dict) -> dict:
    """실외 사진에서 가정이 틀렸을 때의 MAPE."""
    out_rows = [r for r in rows if r["env"] == "outdoor"]

    def run(**kw):
        a = [abs(scale_A(cache[r["file"]][0], cache[r["file"]][1], **kw) / cache[r["file"]][2] - r["true_m"])
             / r["true_m"] * 100 for r in out_rows]
        by = {s: float(np.mean([x for x, r in zip(a, out_rows) if r["site"] == s])) for s in ("site1", "site2")}
        return {"mape": float(np.mean(a)), **by}

    return {"tilt_deg": {t: run(tilt_deg=t) for t in (-3, -2, -1, 0, 1, 2, 3)},
            "height_m": {h: run(h=h) for h in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85)},
            "f_mul": {m: run(f_mul=m) for m in (0.95, 1.0, 1.05)},
            "ground_max_m": {g: run(gmax=g) for g in (3.0, 3.5, 5.0)}}


def per_distance(rs: list[dict], k: str) -> list[tuple]:
    out = []
    for d in sorted({r["true_m"] for r in rs}):
        v = np.array([r[k] for r in rs if r["true_m"] == d])
        out.append((d, float(v.mean()), float(v.std(ddof=1)), level(d), level(float(v.mean()))))
    return out


def report(rows: list[dict], sens: dict) -> tuple[str, dict]:
    res = {"method": __doc__.split("\n\n")[0], "assumptions": {"height_m": H_CAM, "f_px_1280x720": F_RAW,
           "cy_px": CY_RAW, "tilt_deg": 0, "ground_band_m": [1.82, GROUND_MAX_M], "d_far_for_steps": FAR}}
    L = ["# 땅 기준 거리 환산 검증 (자동 생성: `ground_scale.py`)", "",
         f"가정: 렌즈 높이 {H_CAM} m, 수평, 초점거리 {F_RAW:g} px(1280×720), 땅 줄 1.82~{GROUND_MAX_M} m. "
         "상자 거리로 맞춘 값 없음. 핀 단계는 d_far 8 m, 필터 없이.", ""]
    for env in ("outdoor", "indoor"):
        L.append(f"## {'실외' if env == 'outdoor' else '실내'} 사진")
        for site in ("site1", "site2", None):
            rs = [r for r in rows if r["env"] == env and (site is None or r["site"] == site)]
            name = PLACE[(env, site)] if site else "두 곳 합침"
            L.append(f"- **{name}** (n = {len(rs)})")
            for k in METHODS:
                b = block(rs, k)
                res.setdefault(env, {}).setdefault(site or "all", {})[k] = b
                L.append(f"  - {METHODS[k]}: MAPE {b['mape']:.1f}% (중앙 {b['median_ape']:.1f}%), "
                         f"단계 일치 {b['step_exact']:.0f}%, ±1단계 {b['step_pm1']:.0f}%")
        rs = [r for r in rows if r["env"] == env]
        c = compare(rs, "ground", "metric_b")
        res[env]["compare_ground_vs_metric_b"] = c
        L += ["", f"땅 기준 − (실내 모델 − 0.44 m), MAPE 차: 묶음 {c['cluster_n']}개 평균 {c['mape_diff']:+.1f}%p "
              f"(부트스트랩 95% 구간 {c['ci95'][0]:+.1f} ~ {c['ci95'][1]:+.1f}), 땅 기준이 나은 묶음 "
              f"{c['cluster_wins']}/{c['cluster_n']}, 묶음 윌콕슨 p = {c['cluster_wilcoxon_p']:.3g} "
              f"(참고: 사진 {c['photo_n']}장 윌콕슨 p = {c['photo_wilcoxon_p']:.3g}, 5장은 같은 장면이라 독립 아님)", ""]
        L.append("거리별 평균 ± 표준편차 (m), [단계 실제/추정]")
        for site in ("site1", "site2"):
            rs = [r for r in rows if r["env"] == env and r["site"] == site]
            for k in ("ground", "metric_b"):
                pdist = per_distance(rs, k)
                res[env][site][k]["per_distance"] = [dict(zip(("true_m", "mean", "sd", "lv_true", "lv_est"), p))
                                                     for p in pdist]
                L.append(f"- {PLACE[(env, site)]} · {METHODS[k]}: " + ", ".join(
                    f"{d:g} → {m:.2f} ± {s:.2f} [{a}/{b}]" for d, m, s, a, b in pdist))
        L.append("")
    L.append("## 가정이 틀렸을 때 (실외 사진 60장 MAPE, 장소 1 / 장소 2)")
    lab = {"tilt_deg": "기울기 오차 (°, + = 실제로 아래를 봄)", "height_m": "가정한 높이 (m, 실제 0.70)",
           "f_mul": "초점거리 배율", "ground_max_m": "땅 줄 범위 끝 (m)"}
    for k, v in sens.items():
        L.append(f"- {lab[k]}: " + ", ".join(f"{x:g} → {m['mape']:.1f}% ({m['site1']:.1f}/{m['site2']:.1f})"
                                              for x, m in v.items()))
    res["sensitivity"] = {k: {str(x): m for x, m in v.items()} for k, v in sens.items()}
    return "\n".join(L) + "\n", res


def figures(rows: list[dict], sens: dict, res: dict) -> None:
    plt = setup_mpl()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3), sharey=True)
    for ax, site in zip(axes, ("site1", "site2")):
        rs = [r for r in rows if r["env"] == "outdoor" and r["site"] == site]
        for k, mk in (("metric_b", "s"), ("ground", "o")):
            pdist = per_distance(rs, k)
            b = res["outdoor"][site][k]
            ax.errorbar([p[0] for p in pdist], [p[1] for p in pdist], yerr=[p[2] for p in pdist],
                        color=COLOR[k], marker=mk, ms=6, lw=1.8, capsize=2.5, mec="white", mew=1.0,
                        label=f"{METHODS[k]} (MAPE {b['mape']:.0f}%)")
        ax.plot([0, 13], [0, 13], color="#555555", lw=1, ls=":", label="y = x (오차 0)")
        ax.set_xlim(0, 8.5)
        ax.set_ylim(0, 13)
        ax.set_xlabel("줄자 거리 (m)")
        ax.set_title(PLACE[("outdoor", site)], fontsize=10)
        ax.legend(fontsize=8, frameon=False, loc="upper left")
    axes[0].set_ylabel("추정 거리 (m)")
    fig.suptitle("실외 사진: 땅 기준 상대 깊이 대 실내 모델 - 0.44 m (점: 5장 평균, 막대: 표준편차)", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ground_est_vs_true.png")
    plt.close(fig)

    ref = res["outdoor"]["all"]["metric_b"]["mape"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    for ax, k, xl in ((axes[0], "tilt_deg", "기울기 오차 (°)  - 위를 봄 / + 아래를 봄"),
                      (axes[1], "height_m", "가정한 카메라 높이 (m, 실제 0.70)")):
        xs = list(sens[k])
        ax.plot(xs, [sens[k][x]["mape"] for x in xs], color=COLOR["ground"], marker="o", ms=6, lw=2,
                mec="white", mew=1.0, label="땅 기준 상대 깊이")
        ax.axhline(ref, color=COLOR["metric_b"], lw=1.6, ls="--", label=f"실내 모델 - 0.44 m ({ref:.0f}%)")
        ax.set_xlabel(xl)
        ax.legend(fontsize=8, frameon=False, loc="upper left")
    axes[0].set_ylabel("실외 사진 MAPE (%)")
    axes[0].set_ylim(0, None)
    fig.suptitle("가정이 틀렸을 때 실외 오차 (사진 60장)", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ground_sensitivity.png")
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, cache = collect()
    sens = sensitivity(rows, cache)
    text, res = report(rows, sens)
    with (OUT / "ground_rows.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    figures(rows, sens, res)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
