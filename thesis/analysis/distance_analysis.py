#!/usr/bin/env python3
"""
거리 정확도 분석 — 같은 사진을 실내(Hypersim)·실외(Virtual KITTI 2) metric 모델에 넣고
표적(흰 상자 앞면 30×27 cm)의 추정 거리를 줄자 거리와 비교한다. 지시: DISTANCE_TASK.md

  python thesis/analysis/distance_analysis.py            추론(GPU) → exp_distance.csv → 표·그림
  python thesis/analysis/distance_analysis.py --no-infer 이미 만든 exp_distance.csv로 표·그림만

입력
  data/raw/distance_20261017/rois.csv     방법 B: annotate_roi.py 로 표시한 상자 영역(원본 1280×720 좌표)
  ~/tactile-vision/logs/dist_<장소>/probes.csv   방법 A: compare_models.py 클릭 값(있으면 합침)
출력
  data/exp_distance.csv                   사진 × 방법 × 모델 한 줄
  out_distance/                           요약(summary.json, summary.md, 표 CSV), 그림, ROI 확인 이미지

전처리와 모델은 장치 코드를 그대로 쓴다(compare_models.py와 같은 함수):
  1280×720 → crop_rect 가운데 1280×698 → INTER_AREA 924×504, DepthEngine(max_depth 실내 20·실외 80).
값
  roi   상자 영역을 사방 20%씩 줄인 안쪽(가운데 60%×60%) 깊이 중앙값
  click 클릭 지점 5×5 중앙값(compare_models.probe_value). 이 스크립트가 같은 사진으로 다시 계산해 대조한다
  cell_p10_m  ROI 가운데(클릭이면 클릭 지점)가 속한 6×4 셀의 장치 대표값(셀 하위 10%)
보정
  참 거리 ≈ k × 추정 거리, k = Σ(t·e)/Σ(e²) (원점 지나는 최소제곱, 사진 한 장 = 점 하나)
  검증: 같은 장소 안 거리 하나씩 빼고 맞춤(LODO), 장소 교차(장소 1의 k → 장소 2, 반대도)
거리 보정 계수는 분석에서만 쓴다. 장치 설정에 넣지 않는다(설정 동결).
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw" / "distance_20261017"
OUT_CSV = HERE / "data" / "exp_distance.csv"
OUT_DIR = HERE / "out_distance"
DEVICE_REPO = Path.home() / "tactile-vision"

SITES = ("site1_outdoor", "site2_outdoor", "site1_indoor", "site2_indoor")
MODELS = ("indoor", "outdoor")
METHODS = ("roi", "click")
SHRINK = 0.20  # ROI 사방에서 줄이는 비율
DIFF_FLAG = 0.10  # 방법 A·B 차이가 이보다 크면 표시
FIELDS = ["example", "method", "env", "site", "file", "shot", "true_m", "model", "est_m", "cell_p10_m"]
NAME_RE = re.compile(r"^(outdoor|indoor)_(\d+(?:p\d+)?)m_(\d+)_\d+\.png$")
KO_MODEL = {"indoor": "실내 모델(Hypersim)", "outdoor": "실외 모델(VKITTI2)"}
KO_ENV = {"indoor": "실내 사진", "outdoor": "실외 사진"}
COLOR = {"indoor": "#2a78d6", "outdoor": "#eb6834"}  # compare_models 창 색과 같은 계열
MARKER = {"site1": "o", "site2": "s"}

log = logging.getLogger("distance")


# ─────────────────────────────────────────────────────────────
# 입력 읽기
# ─────────────────────────────────────────────────────────────
def parse_name(name: str) -> tuple[str, float, int]:
    """outdoor_1p5m_03_105303.png → ('outdoor', 1.5, 3)"""
    m = NAME_RE.match(name)
    if not m:
        raise ValueError(f"파일 이름 형식이 다름: {name}")
    return m.group(1), float(m.group(2).replace("p", ".")), int(m.group(3))


def load_shots() -> list[dict]:
    """4개 폴더 shots.csv. 파일 이름과 distance_m이 맞는지 확인한다."""
    shots = []
    for folder in SITES:
        with (RAW / folder / "shots.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                env, d, _ = parse_name(r["file"])
                if env != r["scene"] or abs(d - float(r["distance_m"])) > 1e-9:
                    raise ValueError(f"이름과 shots.csv가 다름: {folder}/{r['file']}")
                shots.append({"folder": folder, "site": folder.split("_")[0], "env": env,
                              "file": r["file"], "shot": int(r["shot"]), "true_m": d})
    return shots


def load_rois(keep_empty: bool = False) -> dict[tuple[str, str], tuple[int, int, int, int]]:
    """(폴더, 파일) → (x, y, w, h). 표적 없음(-1)은 keep_empty일 때만 포함한다."""
    p = RAW / "rois.csv"
    out = {}
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            box = tuple(int(r[k]) for k in ("x", "y", "w", "h"))
            if keep_empty or (box[2] > 0 and box[3] > 0):
                out[(r["site"], r["file"])] = box
    return out


def load_probes(root: Path) -> dict[tuple[str, str], dict]:
    """
    방법 A. logs/dist_<폴더>/probes.csv → (폴더, 파일) → 마지막 줄.
    source 열은 'outdoor_2m_01_104902.png (1/30)' 꼴. 클릭 없이 저장한 줄(probe_x 빈칸)은 버린다.
    """
    out = {}
    for folder in SITES:
        p = root / f"dist_{folder}" / "probes.csv"
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                name = r["source"].split(" (")[0].strip()
                if not r["probe_x"]:
                    out.pop((folder, name), None)  # 마지막 줄이 '클릭 없음'이면 그 사진은 빈 값
                    continue
                out[(folder, name)] = {"x": int(r["probe_x"]), "y": int(r["probe_y"]),
                                       "indoor": float(r["indoor_probe_m"]),
                                       "outdoor": float(r["outdoor_probe_m"])}
    return out


# ─────────────────────────────────────────────────────────────
# 추론 (GPU)
# ─────────────────────────────────────────────────────────────
def roi_to_model(box, crop, size) -> tuple[float, float, float, float]:
    """원본 좌표 (x, y, w, h) → 모델 입력 좌표 (실수). crop = crop_rect 결과, size = (W, H)."""
    x, y, w, h = box
    cx, cy, cw, ch = crop
    sx, sy = size[0] / cw, size[1] / ch
    return (x - cx) * sx, (y - cy) * sy, w * sx, h * sy


def inner_slice(mb, size, shrink=SHRINK) -> tuple[slice, slice]:
    """모델 좌표 상자를 사방 shrink만큼 줄인 픽셀 범위. 최소 1픽셀."""
    x, y, w, h = mb
    x0, x1 = x + shrink * w, x + (1 - shrink) * w
    y0, y1 = y + shrink * h, y + (1 - shrink) * h
    W, H = size
    c0, c1 = int(np.clip(round(x0), 0, W - 1)), int(np.clip(round(x1), 1, W))
    r0, r1 = int(np.clip(round(y0), 0, H - 1)), int(np.clip(round(y1), 1, H))
    return slice(r0, max(r1, r0 + 1)), slice(c0, max(c1, c0 + 1))


def cell_of(px: float, py: float, spec, cols: int, rows: int) -> int:
    c = int(np.clip(px // spec.cell_w, 0, cols - 1))
    r = int(np.clip(py // spec.cell_h, 0, rows - 1))
    return r * cols + c


class Device:
    """장치 코드로 두 모델을 만든다(compare_models.py와 같은 방식). GPU를 쓴다."""

    def __init__(self) -> None:
        sys.path.insert(0, str(DEVICE_REPO / "src"))
        sys.path.insert(0, str(DEVICE_REPO / "tools"))
        from tactile_vision import geometry as geo
        from tactile_vision.camera import crop_rect
        from tactile_vision.config import load
        from tactile_vision.depth import DepthEngine
        from compare_models import INDOOR, OUTDOOR, engine_path_for, probe_value

        cfg = load(None)  # ~/tactile-vision/config/default.yaml (읽기만)
        self.spec = spec = cfg.depth.spec
        self.size = (spec.width, spec.height)
        self.geo, self.crop_rect, self.probe_value = geo, crop_rect, probe_value
        self.engines = {}
        for ms in (INDOOR, OUTDOOR):
            p = engine_path_for(ms, None, cfg, spec)
            dcfg = dataclasses.replace(cfg.depth, engine=str(p), max_depth_m=ms.max_depth_m)
            self.engines[ms.key] = DepthEngine(dcfg, cfg.grid, p)
            self.engines[ms.key].warmup(5)
        self.prep = {"input_spec": spec.name, "model_input": list(self.size),
                     "engines": {k: Path(e.dcfg.engine).name for k, e in self.engines.items()},
                     "max_depth_m": {k: e.dcfg.max_depth_m for k, e in self.engines.items()},
                     "grid": f"{geo.GRID_COLS}x{geo.GRID_ROWS}", "cell_px": [spec.cell_w, spec.cell_h],
                     "cell_reducer": f"{cfg.grid.reducer} {cfg.grid.percentile:g}",
                     "cell_margin": cfg.grid.cell_margin}

    def infer(self, path: Path):
        """원본 사진 → (crop, 모델 입력 BGR, {모델: 깊이맵}, {모델: 셀 24개})"""
        raw = cv2.imread(str(path), cv2.IMREAD_COLOR)
        crop = self.crop_rect(raw.shape[1], raw.shape[0], self.size[0] / self.size[1])
        self.prep.setdefault("crop_rect", list(crop))
        x, y, w, h = crop
        img = cv2.resize(raw[y:y + h, x:x + w], self.size, interpolation=cv2.INTER_AREA)
        depth, cells = {}, {}
        for k, e in self.engines.items():
            cells[k] = e.infer(img)
            depth[k] = e.last_depth_map()
            assert depth[k].shape == (self.size[1], self.size[0]), depth[k].shape
        return crop, img, depth, cells


def run_inference(shots, rois, probes) -> tuple[list[dict], list[dict], dict]:
    dev = Device()
    geo, spec, size, probe_value = dev.geo, dev.spec, dev.size, dev.probe_value
    rows, checks = [], []
    for s in shots:
        key = (s["folder"], s["file"])
        if key not in rois and key not in probes:
            continue
        crop, _, depth, cells = dev.infer(RAW / s["folder"] / s["file"])
        base = {"example": 0, "env": s["env"], "site": s["site"], "file": s["file"],
                "shot": s["shot"], "true_m": s["true_m"]}

        if key in rois:
            mb = roi_to_model(rois[key], crop, size)
            sl = inner_slice(mb, size)
            ci = cell_of(mb[0] + mb[2] / 2, mb[1] + mb[3] / 2, spec, geo.GRID_COLS, geo.GRID_ROWS)
            for k in MODELS:
                rows.append({**base, "method": "roi", "model": k,
                             "est_m": round(float(np.median(depth[k][sl])), 4),
                             "cell_p10_m": round(float(cells[k][ci]), 4)})
        if key in probes:
            pr = probes[key]
            ci = cell_of(pr["x"], pr["y"], spec, geo.GRID_COLS, geo.GRID_ROWS)
            for k in MODELS:
                again = probe_value(depth[k], (pr["x"], pr["y"]))
                checks.append({"folder": s["folder"], "file": s["file"], "model": k,
                               "probes_csv": pr[k], "recomputed": round(again, 3)})
                rows.append({**base, "method": "click", "model": k, "est_m": pr[k],
                             "cell_p10_m": round(float(cells[k][ci]), 4)})
    return rows, checks, dev.prep


def write_rows(rows: list[dict]) -> None:
    order = {m: i for i, m in enumerate(METHODS)}
    env_o = {"outdoor": 0, "indoor": 1}
    rows = sorted(rows, key=lambda r: (order[r["method"]], env_o[r["env"]], r["site"],
                                        r["true_m"], r["shot"], r["model"]))
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r[k] for k in FIELDS})


def read_rows() -> list[dict]:
    with OUT_CSV.open(encoding="utf-8") as fh:
        return [{**r, "true_m": float(r["true_m"]), "est_m": float(r["est_m"]), "shot": int(r["shot"]),
                 "cell_p10_m": float(r["cell_p10_m"]) if r["cell_p10_m"] else float("nan")}
                for r in csv.DictReader(fh)]


# ─────────────────────────────────────────────────────────────
# 통계
# ─────────────────────────────────────────────────────────────
def fit_k(t, e) -> float:
    t, e = np.asarray(t, float), np.asarray(e, float)
    return float(np.sum(t * e) / np.sum(e * e))


def mape(t, e) -> float:
    t, e = np.asarray(t, float), np.asarray(e, float)
    return float(np.mean(np.abs(e - t) / t) * 100)


def lodo(rs: list[dict]) -> tuple[list[float], dict[float, float]]:
    """같은 장소 안에서 거리 하나씩 빼고 k를 맞춰 뺀 거리에 적용. (보정 추정값 목록, 거리별 k)"""
    pred, ks = [None] * len(rs), {}
    for d in sorted({r["true_m"] for r in rs}):
        train = [r for r in rs if r["true_m"] != d]
        k = fit_k([r["true_m"] for r in train], [r["est_m"] for r in train])
        ks[d] = k
        for i, r in enumerate(rs):
            if r["true_m"] == d:
                pred[i] = k * r["est_m"]
    return pred, ks


def per_distance(rs: list[dict], corrected: list[float] | None = None) -> list[dict]:
    out = []
    for d in sorted({r["true_m"] for r in rs}):
        idx = [i for i, r in enumerate(rs) if r["true_m"] == d]
        e = np.array([rs[i]["est_m"] for i in idx])
        cp = np.array([rs[i]["cell_p10_m"] for i in idx])
        err = (e - d) / d * 100
        row = {"true_m": d, "n": len(idx), "est_mean_m": e.mean(), "est_sd_m": e.std(ddof=1) if len(e) > 1 else 0.0,
               "err_mean_m": (e - d).mean(), "err_pct_mean": err.mean(),
               "err_pct_sd": err.std(ddof=1) if len(e) > 1 else 0.0, "abs_pct_mean": np.abs(err).mean(),
               "cell_p10_mean_m": float(np.nanmean(cp)) if np.isfinite(cp).any() else float("nan")}
        if corrected is not None:
            c = np.array([corrected[i] for i in idx])
            row["corr_est_mean_m"] = c.mean()
            row["corr_err_pct_mean"] = ((c - d) / d * 100).mean()
            row["corr_abs_pct_mean"] = (np.abs(c - d) / d * 100).mean()
        out.append(row)
    return out


def analyze(rows: list[dict]) -> dict:
    """method × env × model 마다 장소별·합침 통계, LODO, 장소 교차."""
    res = {}
    groups = defaultdict(list)
    for r in rows:
        groups[(r["method"], r["env"], r["model"])].append(r)
    for (method, env, model), rs in sorted(groups.items()):
        g = {"primary": env == model, "sites": {}}
        by_site = defaultdict(list)
        for r in rs:
            by_site[r["site"]].append(r)
        for site, srs in sorted(by_site.items()):
            t = [r["true_m"] for r in srs]
            e = [r["est_m"] for r in srs]
            k = fit_k(t, e)
            pred, ks = lodo(srs)
            g["sites"][site] = {
                "n": len(srs), "k": k, "mape_raw": mape(t, e),
                "mape_in_sample": mape(t, [k * x for x in e]),
                "mape_lodo": mape(t, pred), "k_lodo_range": [min(ks.values()), max(ks.values())],
                "per_distance": per_distance(srs, pred)}
        t = [r["true_m"] for r in rs]
        e = [r["est_m"] for r in rs]
        k_all = fit_k(t, e)
        g["pooled"] = {"n": len(rs), "k": k_all, "mape_raw": mape(t, e),
                       "mape_in_sample": mape(t, [k_all * x for x in e]),
                       "per_distance": per_distance(rs, [k_all * x for x in e])}
        sites = sorted(by_site)
        if len(sites) == 2:
            cross = {}
            for a, b in ((sites[0], sites[1]), (sites[1], sites[0])):
                ka = g["sites"][a]["k"]
                tb = [r["true_m"] for r in by_site[b]]
                eb = [r["est_m"] for r in by_site[b]]
                cross[f"{a}->{b}"] = {"k": ka, "mape_raw": mape(tb, eb),
                                      "mape_corrected": mape(tb, [ka * x for x in eb]),
                                      "per_distance": per_distance(by_site[b], [ka * x for x in eb])}
            g["cross_site"] = cross
        res[f"{method}|{env}|{model}"] = g
    return res


def compare_methods(rows: list[dict]) -> list[dict]:
    """같은 사진·모델의 roi와 click 값이 DIFF_FLAG 넘게 다르면 목록으로."""
    by = defaultdict(dict)
    for r in rows:
        by[(r["env"], r["site"], r["file"], r["model"])][r["method"]] = r
    out = []
    for (env, site, f, model), m in sorted(by.items()):
        if "roi" in m and "click" in m:
            a, b = m["click"]["est_m"], m["roi"]["est_m"]
            rel = (a - b) / b
            if abs(rel) > DIFF_FLAG:
                out.append({"env": env, "site": site, "file": f, "model": model, "true_m": m["roi"]["true_m"],
                            "click_m": a, "roi_m": b, "diff_pct": round(rel * 100, 1)})
    return out


# ─────────────────────────────────────────────────────────────
# 출력: 표
# ─────────────────────────────────────────────────────────────
def write_tables(res: dict, flags: list[dict], checks: list[dict], prep: dict, counts: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump({"preprocess": prep, "counts": counts, "groups": res,
                   "method_diff_over_10pct": flags}, fh, ensure_ascii=False, indent=1, default=float)

    # k 표
    with (OUT_DIR / "k_table.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["method", "env", "model", "primary", "fit", "k", "n", "mape_raw", "mape_corrected",
                     "validation"])
        for key, g in res.items():
            method, env, model = key.split("|")
            for site, s in g["sites"].items():
                wr.writerow([method, env, model, g["primary"], site, f"{s['k']:.4f}", s["n"],
                             f"{s['mape_raw']:.1f}", f"{s['mape_lodo']:.1f}", "LODO"])
                wr.writerow([method, env, model, g["primary"], site, f"{s['k']:.4f}", s["n"],
                             f"{s['mape_raw']:.1f}", f"{s['mape_in_sample']:.1f}", "in-sample"])
            p = g["pooled"]
            wr.writerow([method, env, model, g["primary"], "pooled", f"{p['k']:.4f}", p["n"],
                         f"{p['mape_raw']:.1f}", f"{p['mape_in_sample']:.1f}", "in-sample"])
            for name, c in g.get("cross_site", {}).items():
                wr.writerow([method, env, model, g["primary"], name, f"{c['k']:.4f}", "",
                             f"{c['mape_raw']:.1f}", f"{c['mape_corrected']:.1f}", "cross-site"])

    # 거리별 표
    with (OUT_DIR / "per_distance.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        cols = ["true_m", "n", "est_mean_m", "est_sd_m", "err_mean_m", "err_pct_mean", "err_pct_sd",
                "abs_pct_mean", "cell_p10_mean_m", "corr_est_mean_m", "corr_err_pct_mean", "corr_abs_pct_mean"]
        wr.writerow(["method", "env", "model", "site", "correction"] + cols)
        for key, g in res.items():
            method, env, model = key.split("|")
            for site, s in g["sites"].items():
                for d in s["per_distance"]:
                    wr.writerow([method, env, model, site, "LODO"] + [fmt(d.get(c)) for c in cols])
            for d in g["pooled"]["per_distance"]:
                wr.writerow([method, env, model, "pooled", "in-sample"] + [fmt(d.get(c)) for c in cols])

    # 읽기용 요약
    L = ["# 거리 정확도 요약 (자동 생성: distance_analysis.py)", "",
         f"- 전처리: 원본 1280×720 → crop_rect {prep.get('crop_rect')} → {prep.get('model_input')}, "
         f"엔진 {prep.get('engines')}, max_depth {prep.get('max_depth_m')}",
         f"- 사진 수: {counts}", f"- 값: roi = 상자 영역 사방 {SHRINK:.0%} 줄인 안쪽 중앙값, "
         "click = 클릭 5×5 중앙값. k = Σ(t·e)/Σ(e²)", ""]
    for key, g in res.items():
        method, env, model = key.split("|")
        tag = "주 비교" if g["primary"] else "보조"
        L.append(f"## [{method}] {KO_ENV[env]} × {KO_MODEL[model]} ({tag})")
        for site, s in g["sites"].items():
            L.append(f"- {site}: n {s['n']}, 보정 전 MAPE {s['mape_raw']:.1f}%, k {s['k']:.3f} "
                     f"(LODO k {s['k_lodo_range'][0]:.3f}~{s['k_lodo_range'][1]:.3f}), "
                     f"LODO 보정 후 {s['mape_lodo']:.1f}%, 같은 자료 보정 후 {s['mape_in_sample']:.1f}%")
        p = g["pooled"]
        L.append(f"- 합침: n {p['n']}, 보정 전 {p['mape_raw']:.1f}%, k {p['k']:.3f}, 보정 후 {p['mape_in_sample']:.1f}%")
        for name, c in g.get("cross_site", {}).items():
            L.append(f"- 장소 교차 {name}: k {c['k']:.3f}, 보정 전 {c['mape_raw']:.1f}% → 보정 후 {c['mape_corrected']:.1f}%")
        L.append("- 거리별(장소 합침): " + "; ".join(
            f"{d['true_m']:g} m 추정 {d['est_mean_m']:.2f}±{d['est_sd_m']:.2f} ({d['err_pct_mean']:+.0f}%)"
            for d in p["per_distance"]))
        L.append("")
    if checks:
        dif = [abs(c["probes_csv"] - c["recomputed"]) for c in checks]
        L.append(f"## 클릭 값 재계산 대조: {len(checks)}개, 최대 차이 {max(dif):.3f} m")
        L.append("")
    if flags:
        L.append(f"## 방법 A·B 차이 {DIFF_FLAG:.0%} 초과: {len(flags)}개")
        L += [f"- {f['site']} {f['file']} {f['model']}: click {f['click_m']:.2f} / roi {f['roi_m']:.2f} m "
              f"({f['diff_pct']:+.1f}%)" for f in flags]
    (OUT_DIR / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return "" if not np.isfinite(v) else f"{v:.4f}"
    return str(v)


# ─────────────────────────────────────────────────────────────
# 출력: 그림
# ─────────────────────────────────────────────────────────────
def setup_mpl():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for f in ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
              "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
        if Path(f).exists():
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "NanumGothic", "axes.unicode_minus": False, "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#888888", "axes.grid": True, "grid.color": "#e6e6e6",
                         "grid.linewidth": 0.6, "savefig.dpi": 200, "savefig.bbox": "tight"})
    return plt


def fig_est_vs_true(plt, res: dict, method: str) -> None:
    """추정 대 실제. 왼쪽 실외 사진, 오른쪽 실내 사진. 색 = 모델, 모양 = 장소, 점 = 거리별 평균 ± 표준편차."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for ax, env in zip(axes, ("outdoor", "indoor")):
        top = 0
        for model in MODELS:
            g = res.get(f"{method}|{env}|{model}")
            if not g:
                continue
            for site, s in g["sites"].items():
                pd_ = s["per_distance"]
                x = [d["true_m"] for d in pd_]
                y = [d["est_mean_m"] for d in pd_]
                sd = [d["est_sd_m"] for d in pd_]
                top = max(top, max(np.add(y, sd)))
                ax.errorbar(x, y, yerr=sd, color=COLOR[model], marker=MARKER[site], ms=6, lw=1.6,
                            capsize=2.5, mec="white", mew=1.0,
                            ls="-" if g["primary"] else "--",
                            label=f"{KO_MODEL[model]} · {site.replace('site', '장소 ')}")
        xmax = 8.5 if env == "outdoor" else 4.25
        lim = max(top, xmax) * 1.05
        ax.plot([0, lim], [0, lim], color="#555555", lw=1, ls=":", label="y = x (오차 0)")
        ax.set_xlim(0, xmax)
        ax.set_ylim(0, lim)
        ax.set_xlabel("줄자 거리 (m)")
        ax.set_ylabel("추정 거리 (m)")
        ax.set_title(f"{KO_ENV[env]} ({'실외' if env == 'outdoor' else '실내'} 모델이 주 비교)", fontsize=10)
        ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.suptitle(f"표적까지 추정 거리 대 줄자 거리 — {'상자 영역 중앙값' if method == 'roi' else '클릭 5×5 중앙값'}"
                 " (점: 5장 평균, 막대: 표준편차)", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_est_vs_true_{method}.png")
    plt.close(fig)


def fig_error(plt, res: dict, method: str) -> None:
    """주 비교(같은 환경 모델)의 거리별 오차 %: 보정 전 vs LODO 보정 후, 장소별."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), sharey=False)
    for ax, env in zip(axes, ("outdoor", "indoor")):
        g = res.get(f"{method}|{env}|{env}")
        if not g:
            continue
        for site, s in g["sites"].items():
            pd_ = s["per_distance"]
            x = np.array([d["true_m"] for d in pd_])
            off = -0.04 if site == "site1" else 0.04
            sc = x * (1 + off)
            ax.errorbar(sc, [d["err_pct_mean"] for d in pd_], yerr=[d["err_pct_sd"] for d in pd_],
                        color=COLOR[env], marker=MARKER[site], ms=6, lw=1.4, capsize=2.5, mec="white",
                        label=f"보정 전 · {site.replace('site', '장소 ')}")
            ax.plot(sc, [d["corr_err_pct_mean"] for d in pd_], color="#52514e", marker=MARKER[site],
                    ms=6, lw=1.2, ls="--", mfc="white",
                    label=f"보정 후(LODO) · {site.replace('site', '장소 ')}")
        ax.axhline(0, color="#555555", lw=1, ls=":")
        ax.set_xscale("log")
        ticks = sorted({d["true_m"] for s in g["sites"].values() for d in s["per_distance"]})
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t:g}" for t in ticks])
        ax.minorticks_off()
        ax.set_xlabel("줄자 거리 (m, 로그 눈금)")
        ax.set_ylabel("오차 (%) = (추정 - 실제) / 실제")
        ax.set_title(f"{KO_ENV[env]} × {KO_MODEL[env]}", fontsize=10)
        hs, ls = ax.get_legend_handles_labels()
        order = sorted(range(len(ls)), key=lambda i: (not ls[i].startswith("보정 전"), ls[i]))
        ax.legend([hs[i] for i in order], [ls[i] for i in order], fontsize=7.5, frameon=False)
    fig.suptitle(f"거리별 오차 — 보정 전과 거리 하나씩 빼고 맞춘 k로 보정한 뒤 ({method})", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_error_pct_{method}.png")
    plt.close(fig)


def roi_sheets(rois: dict, shots: list[dict]) -> list[Path]:
    """ROI 확인용 모음: 환경마다 1장. 행 = 거리, 열 = 장소 1의 1~5번 | 장소 2의 1~5번.
    칸마다 ROI 주변을 잘라 확대하고, ROI(초록)와 실제 값을 읽는 안쪽 60%(노랑)를 그린다."""
    TW, TH, LAB = 200, 150, 18
    paths = []
    for env in ("outdoor", "indoor"):
        ss = [s for s in shots if s["env"] == env]
        dists = sorted({s["true_m"] for s in ss})
        cols = [(site, k) for site in ("site1", "site2") for k in range(1, 6)]
        H = 30 + len(dists) * (TH + LAB)
        W = 50 + len(cols) * TW + 10
        sheet = np.full((H, W, 3), 255, np.uint8)
        for ci, (site, k) in enumerate(cols):
            cv2.putText(sheet, f"{site} #{k}", (50 + ci * TW + 60, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (40, 40, 40), 1, cv2.LINE_AA)
        for ri, d in enumerate(dists):
            y0 = 30 + ri * (TH + LAB)
            cv2.putText(sheet, f"{d:g}m", (4, y0 + TH // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1,
                        cv2.LINE_AA)
            for ci, (site, k) in enumerate(cols):
                x0 = 50 + ci * TW
                s = next((s for s in ss if s["site"] == site and s["true_m"] == d and s["shot"] == k), None)
                if s is None:
                    continue
                key = (s["folder"], s["file"])
                img = cv2.imread(str(RAW / s["folder"] / s["file"]))
                if key not in rois or rois[key][2] <= 0:
                    tile = cv2.resize(img, (TW - 4, TH - 4), interpolation=cv2.INTER_AREA)
                    msg = "not yet" if key not in rois else "NO TARGET (c)"
                    cv2.putText(tile, msg, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    sheet[y0 + 2:y0 + TH - 2, x0 + 2:x0 + TW - 2] = tile
                    continue
                bx, by, bw, bh = rois[key]
                # ROI의 2배 영역(최소 160×120)을 4:3으로 잘라 확대
                cw = max(bw * 2.0, bh * 2.0 * 4 / 3, 160)
                ch = cw * 3 / 4
                cx, cy = bx + bw / 2, by + bh / 2
                X0 = int(np.clip(cx - cw / 2, 0, img.shape[1] - cw))
                Y0 = int(np.clip(cy - ch / 2, 0, img.shape[0] - ch))
                X1, Y1 = int(min(img.shape[1], X0 + cw)), int(min(img.shape[0], Y0 + ch))
                X0, Y0 = max(0, X0), max(0, Y0)
                crop = img[Y0:Y1, X0:X1]
                sc = (TW - 4) / crop.shape[1]
                tile = cv2.resize(crop, (TW - 4, int(round(crop.shape[0] * sc))), interpolation=cv2.INTER_AREA)
                tile = tile[:TH - 4]

                def rect(x, y, w, h, col, t):
                    p0 = (int(round((x - X0) * sc)), int(round((y - Y0) * sc)))
                    p1 = (int(round((x + w - X0) * sc)), int(round((y + h - Y0) * sc)))
                    cv2.rectangle(tile, p0, p1, col, t, cv2.LINE_AA)

                rect(bx, by, bw, bh, (0, 200, 0), 2)
                rect(bx + SHRINK * bw, by + SHRINK * bh, (1 - 2 * SHRINK) * bw, (1 - 2 * SHRINK) * bh,
                     (0, 215, 255), 1)
                sheet[y0 + 2:y0 + 2 + tile.shape[0], x0 + 2:x0 + 2 + tile.shape[1]] = tile
                cv2.putText(sheet, f"{bw}x{bh}px", (x0 + 4, y0 + TH + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (90, 90, 90), 1, cv2.LINE_AA)
        p = OUT_DIR / f"roi_check_{env}.jpg"
        cv2.imwrite(str(p), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        paths.append(p)
    return paths


# ─────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-infer", action="store_true", help="추론 없이 기존 exp_distance.csv로 표·그림만")
    ap.add_argument("--probes-root", default=str(DEVICE_REPO / "logs"),
                    help="방법 A probes.csv가 있는 폴더(그 아래 dist_<장소>/probes.csv)")
    ap.add_argument("--sheets-only", action="store_true", help="ROI 확인 이미지만 만들고 끝")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shots = load_shots()
    rois = load_rois()
    sheets = roi_sheets(load_rois(keep_empty=True), shots)
    print("ROI 확인 이미지:", *map(str, sheets))
    if args.sheets_only:
        return 0

    probes = load_probes(Path(args.probes_root).expanduser())
    checks, prep = [], {}
    if args.no_infer:
        rows = read_rows()
        if (OUT_DIR / "summary.json").exists():
            prep = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8")).get("preprocess", {})
    else:
        rows, checks, prep = run_inference(shots, rois, probes)
        write_rows(rows)
        rows = read_rows()
    counts = {m: len({(r["site"], r["env"], r["file"]) for r in rows if r["method"] == m}) for m in METHODS}
    print(f"사진 수: 방법 B(roi) {counts['roi']}장, 방법 A(click) {counts['click']}장 / 전체 {len(shots)}장")

    res = analyze(rows)
    flags = compare_methods(rows)
    write_tables(res, flags, checks, prep, counts)
    plt = setup_mpl()
    for m in METHODS:
        if any(k.startswith(m + "|") for k in res):
            fig_est_vs_true(plt, res, m)
            fig_error(plt, res, m)
    if checks:
        worst = max(abs(c["probes_csv"] - c["recomputed"]) for c in checks)
        print(f"클릭 값 재계산 대조: {len(checks)}개, 최대 차이 {worst:.3f} m")
    print((OUT_DIR / "summary.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
