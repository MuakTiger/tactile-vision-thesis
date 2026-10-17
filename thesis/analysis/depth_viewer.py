#!/usr/bin/env python3
"""
거리 정확도 사진 뷰어 — 사진마다 두 모델의 깊이맵과 ROI 값을 한 장씩 넘겨 본다.

  python thesis/analysis/depth_viewer.py --build            처음 한 번: 120장 추론(GPU) → data/depth_cache/
  python thesis/analysis/relative_depth.py --build          땅 기준 보기용 상대깊이(GPU) → 같은 캐시에 *_rel.npy
  python thesis/analysis/depth_viewer.py                    보기 (GPU 안 씀, 미리 계산한 깊이맵만 읽음)
  python thesis/analysis/depth_viewer.py --start site2_indoor     그 폴더(또는 파일 이름 일부)부터

보기 (m 키로 바꿈)
  땅 기준   아래 왼쪽 = 상대깊이 + 땅 기준 환산(ground_scale.py와 같은 계산, 실외용)
            아래 오른쪽 = 실내 모델 − 0.44 m(실내용). 입력 위 점선 = 그 줄에 보이는 땅의 거리(높이 0.70 m·수평)
  metric    아래 = 실내 모델(Hypersim) | 실외 모델(VKITTI2), 보정 없음 (예전 보기)

창 구성
  왼쪽 위    모델 입력 924×504(장치와 같은 전처리) + ROI(초록)·값을 읽는 안쪽 60%(노랑)·ROI 가운데 셀(하늘색)
  오른쪽 위  줄자 거리, 모델별 ROI 통계, 같은 거리 5장, 클릭한 픽셀 값
  아래       두 깊이맵 (같은 색 범위, 6×4 셀 격자)

키
  n / p      다음 / 이전 사진            ] / [   다음 / 이전 거리(5장 묶음)
  1 ~ 4      폴더로 이동(실외 1 · 실외 2 · 실내 1 · 실내 2)
  m          보기 바꾸기 (땅 기준 ↔ metric)
  c          색 범위 0.5~8 → 0.5~20 → 0.5~80 m
  왼쪽 클릭   그 픽셀의 두 모델 깊이(세 그림 어디를 눌러도 같은 점)     오른쪽 클릭  해제
  q / ESC    종료

값은 distance_analysis.py와 같은 함수(roi_to_model, inner_slice, cell_of)로 계산한다 → exp_distance.csv와 같은 숫자.
깊이맵 캐시(약 0.5 GB)는 git에 넣지 않는다(.gitignore).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from distance_analysis import (  # noqa: E402
    OUT_CSV, OUT_DIR, RAW, SHRINK, SITES, cell_of, inner_slice, load_rois, load_shots, roi_to_model)
from relative_depth import B_INDOOR, CY_RAW, F_RAW, GROUND_MAX_M, H_CAM  # noqa: E402

CACHE = HERE / "data" / "depth_cache"
GROUND_CSV = OUT_DIR / "ground" / "ground_rows.csv"
WIN = "distance viewer"
PW, PH = 924, 504  # 모델 입력 = 패널 크기
TITLE_H = 30
BG = (26, 26, 26)
RANGES = [(0.5, 8.0), (0.5, 20.0), (0.5, 80.0)]
MODELS = ("indoor", "outdoor")  # 캐시에 저장된 metric 모델
VIEWS = (("ground", "indoor_b"), ("indoor", "outdoor"))  # m 키로 바꿈. 앞이 기본
TITLE = {"indoor": "실내 모델 (Hypersim, max 20 m)", "outdoor": "실외 모델 (Virtual KITTI 2, max 80 m)",
         "ground": "땅 기준 상대깊이 (렌즈 0.70 m · 수평) — 실외용",
         "indoor_b": "실내 모델 - 0.44 m — 실내용"}  # NanumGothic에 '−'(U+2212)가 없어 '-'
SHORT = {"indoor": "실내 모델", "outdoor": "실외 모델", "ground": "땅 기준", "indoor_b": "실내 모델 - 0.44"}
GROUND_MARKS = (2.0, 3.0, 4.0, 6.0, 8.0)  # 입력 위에 표시할 땅 거리
PLACE = {"site1_outdoor": "실외 1 · 산책로", "site2_outdoor": "실외 2 · 주차장",
         "site1_indoor": "실내 1 · 거실", "site2_indoor": "실내 2 · 주방"}
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
FONT_B = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
PROBE_HALF = 2  # 5×5 (compare_models.py와 같음)


def cache_path(s: dict) -> Path:
    return CACHE / s["folder"] / (Path(s["file"]).stem + ".npz")


def ordered_shots() -> list[dict]:
    shots = load_shots()
    fi = {f: i for i, f in enumerate(SITES)}
    return sorted(shots, key=lambda s: (fi[s["folder"]], s["true_m"], s["shot"]))


# ─────────────────────────────────────────────────────────────
# 미리 계산 (GPU)
# ─────────────────────────────────────────────────────────────
def build(rebuild: bool) -> int:
    from distance_analysis import Device

    shots = ordered_shots()
    todo = [s for s in shots if rebuild or not cache_path(s).exists()]
    print(f"사진 {len(shots)}장, 계산할 것 {len(todo)}장 → {CACHE}")
    if not todo:
        return 0
    dev = Device()
    for i, s in enumerate(todo, 1):
        crop, img, depth, cells = dev.infer(RAW / s["folder"] / s["file"])
        p = cache_path(s)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(p, input_bgr=img, crop=np.array(crop),
                            **{f"{k}_depth_m": depth[k] for k in MODELS},
                            **{f"{k}_cells_m": cells[k] for k in MODELS})
        if i % 10 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)} {s['folder']}/{s['file']}")
    (CACHE / "meta.json").write_text(json.dumps({**dev.prep, "photos": len(shots)}, ensure_ascii=False,
                                                indent=1), encoding="utf-8")
    return 0


# ─────────────────────────────────────────────────────────────
# 계산 (CPU)
# ─────────────────────────────────────────────────────────────
def roi_stats(depth: np.ndarray, cells: np.ndarray, box, crop) -> dict:
    size = (PW, PH)
    mb = roi_to_model(box, crop, size)
    sl = inner_slice(mb, size)
    full = inner_slice(mb, size, shrink=0.0)
    v = depth[sl].ravel()
    ci = cell_of(mb[0] + mb[2] / 2, mb[1] + mb[3] / 2, _CellSpec, 6, 4)
    return {"mb": mb, "sl": sl, "n": v.size, "median": float(np.median(v)), "mean": float(v.mean()),
            "sd": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "p10": float(np.percentile(v, 10)), "p25": float(np.percentile(v, 25)),
            "p75": float(np.percentile(v, 75)), "full_median": float(np.median(depth[full])),
            "cell": ci, "cell_val": float(cells[ci])}


class _CellSpec:  # cell_of가 쓰는 셀 크기 (924/6, 504/4)
    cell_w, cell_h = PW // 6, PH // 4


def probe(depth: np.ndarray, x: int, y: int) -> tuple[float, float]:
    patch = depth[max(0, y - PROBE_HALF): y + PROBE_HALF + 1, max(0, x - PROBE_HALF): x + PROBE_HALF + 1]
    return float(depth[y, x]), float(np.median(patch))


def load_groups() -> dict:
    """exp_distance.csv(방법 roi) + ground_rows.csv → (env, site, true_m, model) → [사진별 값] (shot 순)"""
    g = defaultdict(list)
    if OUT_CSV.exists():
        with OUT_CSV.open(encoding="utf-8") as fh:
            rows = [r for r in csv.DictReader(fh) if r["method"] == "roi"]
        for r in sorted(rows, key=lambda r: int(r["shot"])):
            g[(r["env"], r["site"], float(r["true_m"]), r["model"])].append(float(r["est_m"]))
    if GROUND_CSV.exists():
        with GROUND_CSV.open(encoding="utf-8") as fh:
            rows = sorted(csv.DictReader(fh), key=lambda r: r["file"])  # 파일 이름 = 거리_번호_시각
        for r in rows:
            for k, col in (("ground", "ground"), ("indoor_b", "metric_b")):
                g[(r["env"], r["site"], float(r["true_m"]), k)].append(float(r[col]))
    return g


def cells_p10(depth: np.ndarray) -> np.ndarray:
    """장치 셀 대표값과 같은 식: 6×4 셀마다 k = round(0.1 n)번째로 작은 값."""
    ch, cw = PH // 4, PW // 6
    b = depth.reshape(4, ch, 6, cw).transpose(0, 2, 1, 3).reshape(24, -1)
    k = max(1, int(round(b.shape[1] * 0.10)))
    return np.partition(b, k - 1, axis=1)[:, k - 1]


def ground_geom(crop) -> tuple[float, float]:
    """모델 입력 좌표의 초점거리 f와 수평선 줄 y0 (ground_scale.py와 같은 가정)."""
    _, cy, _, ch = crop
    return F_RAW * PH / ch, (CY_RAW - cy) * PH / ch


def add_derived(z: dict) -> None:
    """캐시에서 땅 기준 깊이맵과 실내 − 0.44 m 깊이맵을 만든다(ground_scale.scale_A와 같은 계산)."""
    from ground_scale import scale_A

    crop = tuple(int(v) for v in z["crop"])
    z["indoor_b_depth_m"] = np.maximum(z["indoor_depth_m"] + B_INDOOR, 0.01)
    if "rel" in z:
        z["ground_A"] = scale_A(z["rel"], crop)
        z["ground_depth_m"] = z["ground_A"] / np.maximum(z["rel"], 1e-6)
    else:
        z["ground_A"] = float("nan")
        z["ground_depth_m"] = np.full((PH, PW), np.nan, np.float32)
    for k in ("indoor_b", "ground"):
        z[f"{k}_cells_m"] = cells_p10(z[f"{k}_depth_m"])


def colorize(depth: np.ndarray, near: float, far: float) -> np.ndarray:
    """장치 viz.colorize_depth와 같은 식(고정 범위, 가까우면 빨강 · 멀면 파랑)."""
    d = np.clip(depth, near, far)
    return cv2.applyColorMap(((far - d) / (far - near) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)


# ─────────────────────────────────────────────────────────────
# 그리기
# ─────────────────────────────────────────────────────────────
class Text:
    """한글은 cv2.putText로 못 그려서 PIL로 한 번에 그린다."""

    def __init__(self) -> None:
        from PIL import ImageFont

        self._f = {}
        self._font = lambda size, bold: self._f.setdefault(
            (size, bold), ImageFont.truetype(FONT_B if bold else FONT, size))
        self.items: list = []

    def add(self, xy, text, size=16, color=(235, 235, 235), bold=False, outline=False) -> None:
        self.items.append((xy, text, size, color, bold, outline))

    def draw(self, canvas: np.ndarray) -> np.ndarray:
        from PIL import Image, ImageDraw

        im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        dr = ImageDraw.Draw(im)
        for xy, text, size, color, bold, outline in self.items:
            kw = {"stroke_width": 2, "stroke_fill": (0, 0, 0)} if outline else {}
            dr.text(xy, text, font=self._font(size, bold), fill=color, **kw)
        self.items = []
        return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def rect(img, x, y, w, h, color, t) -> None:
    cv2.rectangle(img, (int(round(x)), int(round(y))), (int(round(x + w)), int(round(y + h))), color, t,
                  cv2.LINE_AA)


def overlay(img: np.ndarray, st: dict | None, probe_xy, grid: bool) -> None:
    if grid:
        for c in range(1, 6):
            cv2.line(img, (c * _CellSpec.cell_w, 0), (c * _CellSpec.cell_w, PH), (60, 60, 60), 1)
        for r in range(1, 4):
            cv2.line(img, (0, r * _CellSpec.cell_h), (PW, r * _CellSpec.cell_h), (60, 60, 60), 1)
    if st is not None:
        r, c = divmod(st["cell"], 6)
        rect(img, c * _CellSpec.cell_w, r * _CellSpec.cell_h, _CellSpec.cell_w - 1, _CellSpec.cell_h - 1,
             (230, 200, 60), 1)
        x, y, w, h = st["mb"]
        rect(img, x, y, w, h, (0, 200, 0), 2)
        sy, sx = st["sl"]
        rect(img, sx.start, sy.start, sx.stop - sx.start - 1, sy.stop - sy.start - 1, (0, 215, 255), 1)
    if probe_xy is not None:
        px, py = probe_xy
        for col, t in (((0, 0, 0), 3), ((255, 255, 255), 1)):
            cv2.line(img, (px - 12, py), (px - 4, py), col, t)
            cv2.line(img, (px + 4, py), (px + 12, py), col, t)
            cv2.line(img, (px, py - 12), (px, py - 4), col, t)
            cv2.line(img, (px, py + 4), (px, py + 12), col, t)
            rect(img, px - PROBE_HALF, py - PROBE_HALF, 2 * PROBE_HALF, 2 * PROBE_HALF, col, 1)


def colorbar(img: np.ndarray, near: float, far: float, tx: Text, ox: int, oy: int) -> None:
    w, h, x0, y0 = 260, 10, 12, PH - 26
    ramp = np.linspace(near, far, w, dtype=np.float32)[None, :].repeat(h, 0)
    img[y0:y0 + h, x0:x0 + w] = colorize(ramp, near, far)
    cv2.rectangle(img, (x0 - 1, y0 - 1), (x0 + w, y0 + h), (20, 20, 20), 1)
    tx.add((ox + x0, oy + y0 - 18), f"{near:g} m", 13, outline=True)
    tx.add((ox + x0 + w - 36, oy + y0 - 18), f"{far:g} m", 13, outline=True)


def pct(est: float, true: float) -> str:
    return f"{(est - true) / true * 100:+.0f}%"


class Viewer:
    def __init__(self, start: str | None, scale: float) -> None:
        self.shots = [s for s in ordered_shots() if cache_path(s).exists()]
        if not self.shots:
            raise SystemExit("깊이맵 캐시가 없음 — 먼저: python thesis/analysis/depth_viewer.py --build")
        self.rois = load_rois()
        self.groups = load_groups()
        self.i = 0
        if start:
            self.i = next((j for j, s in enumerate(self.shots)
                           if start in s["folder"] or start in s["file"]), 0)
        self.scale = scale
        self.range_idx = 0
        self.view = 0
        self.probe = None
        self.dirty = True
        self.tx = Text()
        self._cache: dict[int, dict] = {}

    # 사진 하나 읽기 (최근 몇 장은 메모리에 둔다)
    def data(self) -> dict:
        if self.i not in self._cache:
            p = cache_path(self.shots[self.i])
            z = np.load(p)
            d = {k: z[k] for k in z.files}
            rel = p.with_name(p.stem + "_rel.npy")
            if rel.exists():
                d["rel"] = np.load(rel).astype(np.float32)
            add_derived(d)
            self._cache[self.i] = d
            for k in list(self._cache)[:-6]:
                del self._cache[k]
        return self._cache[self.i]

    def go(self, i: int) -> None:
        self.i = i % len(self.shots)
        self.probe = None
        self.dirty = True

    def jump_distance(self, d: int) -> None:
        """같은 (폴더, 거리) 묶음의 첫 장들 사이를 이동한다."""
        starts = [j for j, s in enumerate(self.shots)
                  if j == 0 or (s["folder"], s["true_m"]) != (self.shots[j - 1]["folder"],
                                                              self.shots[j - 1]["true_m"])]
        cur = max(k for k, j in enumerate(starts) if j <= self.i)
        self.go(starts[(cur + d) % len(starts)])

    def on_mouse(self, event, x, y, _f, _p) -> None:
        y_top, y_bot = TITLE_H, 2 * TITLE_H + PH
        if event == cv2.EVENT_LBUTTONDOWN:
            if y_top <= y < y_top + PH and x < PW:
                self.probe = (x, y - y_top)
            elif y_bot <= y < y_bot + PH and x < 2 * PW:
                self.probe = (x % PW, y - y_bot)
            else:
                return
            self.dirty = True
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.probe = None
            self.dirty = True

    def render(self) -> np.ndarray:
        s, z, tx = self.shots[self.i], self.data(), self.tx
        crop = tuple(int(v) for v in z["crop"])
        box = self.rois.get((s["folder"], s["file"]))
        models = VIEWS[self.view]
        depth = {k: z[f"{k}_depth_m"] for k in models}
        stats = {k: roi_stats(depth[k], z[f"{k}_cells_m"], box, crop) for k in models} if box else {}
        near, far = RANGES[self.range_idx]
        f, y0 = ground_geom(crop)
        band_top = int(np.ceil(y0 + f * H_CAM / GROUND_MAX_M))  # 배율 계산에 쓰는 땅 줄 시작

        H = 2 * (TITLE_H + PH)
        canvas = np.full((H, 2 * PW, 3), BG, np.uint8)

        # 왼쪽 위: 모델 입력
        img = z["input_bgr"].copy()
        overlay(img, stats.get(models[0]), self.probe, grid=False)
        if self.view == 0:  # 그 줄에 보이는 땅의 거리 (렌즈 0.70 m·수평 가정)
            for dist in GROUND_MARKS:
                yy = int(round(y0 + f * H_CAM / dist))
                for xx in range(0, PW, 16):
                    cv2.line(img, (xx, yy), (xx + 8, yy), (255, 255, 255), 1, cv2.LINE_AA)
                tx.add((PW - 70, TITLE_H + yy - 18), f"땅 {dist:g} m", 13, outline=True)
        canvas[TITLE_H:TITLE_H + PH, :PW] = img
        tx.add((10, 5), "모델 입력 924×504  ·  초록 ROI, 노랑 = 값을 읽는 안쪽 60%, 하늘색 = ROI 가운데 셀"
                        + ("  ·  점선 = 그 줄의 땅 거리" if self.view == 0 else ""), 15)

        # 아래: 깊이맵 2개
        yb = 2 * TITLE_H + PH
        for j, k in enumerate(models):
            ox = j * PW
            dm = colorize(depth[k], near, far)
            overlay(dm, stats.get(k), self.probe, grid=True)
            colorbar(dm, near, far, tx, ox, yb)
            if k == "ground":  # 배율 A를 계산한 땅 줄(1.82~3.5 m) 표시
                cv2.rectangle(dm, (2, band_top), (PW - 3, PH - 2), (255, 255, 255), 1)
                tx.add((ox + PW - 300, yb + band_top - 20),
                       f"배율 계산 땅 줄 (1.82~{GROUND_MAX_M:g} m)  A = {z['ground_A']:.2f}", 13, outline=True)
            canvas[yb:yb + PH, ox:ox + PW] = dm
            primary = self.primary(k, s)
            tx.add((ox + 10, yb - TITLE_H + 5), TITLE[k] + ("   ← 이 사진의 주 비교" if primary else "   (보조)"),
                   15, bold=primary, color=(255, 200, 120) if primary else (200, 200, 200))
            if k in stats:
                x, y, w, h = stats[k]["mb"]
                tx.add((ox + int(x), yb + max(0, int(y) - 24)), f"{stats[k]['median']:.2f} m", 17, bold=True,
                       outline=True)

        self.info(canvas, s, stats, depth, crop)
        return tx.draw(canvas)

    def primary(self, k: str, s: dict) -> bool:
        """이 사진에서 주로 볼 모델: 땅 기준 보기는 실외 = 땅 기준, 실내 = 실내 − 0.44 m."""
        if self.view == 0:
            return k == ("ground" if s["env"] == "outdoor" else "indoor_b")
        return k == s["env"]

    def info(self, canvas, s, stats, depth, crop) -> None:
        tx, x0, t = self.tx, PW + 18, s["true_m"]
        ka, kb = VIEWS[self.view]
        c1, c2 = x0 + 330, x0 + 600
        dim, hi = (170, 170, 170), (255, 255, 255)
        y = 8
        tx.add((x0, y), f"[{self.i + 1}/{len(self.shots)}]  {PLACE[s['folder']]}", 20, bold=True)
        y += 30
        tx.add((x0, y), f"{s['folder']}/{s['file']}", 14, color=dim)
        y += 24
        tx.add((x0, y), f"줄자 거리  {t:g} m      ·      같은 거리 5장 중 {s['shot']}번", 18, bold=True,
               color=(140, 230, 140))
        y += 34
        if not stats:
            tx.add((x0, y), "이 사진은 ROI가 없음", 16)
            return
        bx, by, bw, bh = self.rois[(s["folder"], s["file"])]
        mx, my, mw, mh = stats[ka]["mb"]
        tx.add((x0, y), f"ROI 원본 {bx},{by} {bw}×{bh} px  →  모델 {mx:.0f},{my:.0f} {mw:.0f}×{mh:.0f} px"
                        f"  ·  읽는 픽셀 {stats[ka]['n']}개", 14, color=dim)
        y += 30

        tx.add((c1, y), SHORT[ka], 16, bold=True, color=(255, 200, 120) if self.primary(ka, s) else hi)
        tx.add((c2, y), SHORT[kb], 16, bold=True, color=(255, 200, 120) if self.primary(kb, s) else hi)
        y += 28
        a, b = stats[ka], stats[kb]
        rows = [
            (f"분석값: 안쪽 {1 - 2 * SHRINK:.0%} 중앙값", f"{a['median']:.2f} m  ({pct(a['median'], t)})",
             f"{b['median']:.2f} m  ({pct(b['median'], t)})", True),
            ("  평균 ± 표준편차", f"{a['mean']:.2f} ± {a['sd']:.2f}", f"{b['mean']:.2f} ± {b['sd']:.2f}", False),
            ("  하위 10%", f"{a['p10']:.2f}", f"{b['p10']:.2f}", False),
            ("  25~75% 범위", f"{a['p25']:.2f} ~ {a['p75']:.2f}", f"{b['p25']:.2f} ~ {b['p75']:.2f}", False),
            ("  ROI 전체(줄이기 전) 중앙값", f"{a['full_median']:.2f}", f"{b['full_median']:.2f}", False),
            (f"  장치 셀 값(하위 10%, 셀 {a['cell'] // 6 + 1}행 {a['cell'] % 6 + 1}열)", f"{a['cell_val']:.2f}",
             f"{b['cell_val']:.2f}", False),
        ]
        for label, va, vb, strong in rows:
            tx.add((x0, y), label, 15, color=hi if strong else dim, bold=strong)
            tx.add((c1, y), va, 16 if strong else 15, bold=strong)
            tx.add((c2, y), vb, 16 if strong else 15, bold=strong)
            y += 26 if strong else 23
        y += 10

        # 같은 거리 5장 (exp_distance.csv)
        tx.add((x0, y), f"같은 거리 {t:g} m의 5장 (이 장소)", 15, bold=True)
        y += 25
        for label, fn in (("  평균 ± 표준편차", lambda v: f"{np.mean(v):.2f} ± {np.std(v, ddof=1):.2f}"),
                          ("  사진별 값", lambda v: "  ".join(f"{x:.1f}" for x in v))):
            tx.add((x0, y), label, 15, color=dim)
            for col, k in ((c1, ka), (c2, kb)):
                v = self.groups.get((s["env"], s["site"], t, k), [])
                tx.add((col, y), fn(v) if len(v) > 1 else "-", 15)
            y += 23
        y += 14

        # 클릭
        if self.probe is None:
            tx.add((x0, y), "클릭: 세 그림 어디든 왼쪽 클릭하면 그 픽셀의 두 모델 깊이를 보여 줌", 15, color=dim)
            y += 23
        else:
            px, py = self.probe
            ox = px * crop[2] / PW + crop[0]
            oy = py * crop[3] / PH + crop[1]
            tx.add((x0, y), f"클릭  모델 ({px}, {py})  ·  원본 약 ({ox:.0f}, {oy:.0f})", 15, bold=True)
            y += 25
            pa, pb = probe(depth[ka], px, py), probe(depth[kb], px, py)
            for label, j in (("  그 픽셀", 0), ("  5×5 중앙값", 1)):
                tx.add((x0, y), label, 15, color=dim)
                tx.add((c1, y), f"{pa[j]:.2f} m  ({pct(pa[j], t)})", 15)
                tx.add((c2, y), f"{pb[j]:.2f} m  ({pct(pb[j], t)})", 15)
                y += 23
            tx.add((x0, y), "  (오차 %는 줄자 거리 기준 — 상자 밖을 누르면 의미 없음)", 13, color=dim)
            y += 22

        keys = (f"n/p 사진   ]/[ 거리   1~4 폴더   m 보기({'땅 기준' if self.view == 0 else 'metric'})   "
                f"c 색 범위({RANGES[self.range_idx][0]:g}~{RANGES[self.range_idx][1]:g} m)   "
                "클릭 읽기 · 오른쪽 해제   q 종료")
        tx.add((x0, TITLE_H + PH - 22), keys, 13, color=dim)

    def run(self) -> None:
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(WIN, int(2 * PW * self.scale), int(2 * (TITLE_H + PH) * self.scale))
        cv2.setMouseCallback(WIN, self.on_mouse)
        folders = [next(j for j, s in enumerate(self.shots) if s["folder"] == f) if
                   any(s["folder"] == f for s in self.shots) else None for f in SITES]
        while True:
            if self.dirty:
                self.dirty = False
                cv2.imshow(WIN, self.render())
                s = self.shots[self.i]
                cv2.setWindowTitle(WIN, f"[{self.i + 1}/{len(self.shots)}] {s['folder']}/{s['file']}")
            key = cv2.waitKey(30) & 0xFF
            if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key in (ord("q"), 27):
                break
            if key == ord("n"):
                self.go(self.i + 1)
            elif key == ord("p"):
                self.go(self.i - 1)
            elif key == ord("]"):
                self.jump_distance(+1)
            elif key == ord("["):
                self.jump_distance(-1)
            elif key == ord("c"):
                self.range_idx = (self.range_idx + 1) % len(RANGES)
                self.dirty = True
            elif key == ord("m"):
                self.view = (self.view + 1) % len(VIEWS)
                self.dirty = True
            elif ord("1") <= key <= ord("4") and folders[key - ord("1")] is not None:
                self.go(folders[key - ord("1")])
        cv2.destroyAllWindows()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="깊이맵 미리 계산(GPU). 이미 있는 사진은 건너뜀")
    ap.add_argument("--rebuild", action="store_true", help="--build 때 있는 것도 다시 계산")
    ap.add_argument("--start", default=None, help="시작할 폴더 이름 또는 파일 이름 일부")
    ap.add_argument("--scale", type=float, default=1.0, help="창 크기 배율 (기본 1.0 = 1848×1068)")
    ap.add_argument("--snapshot", default=None, metavar="PNG",
                    help="창 없이 시작 사진 1장을 그려 저장하고 끝 (확인용)")
    ap.add_argument("--view", type=int, default=0, choices=range(len(VIEWS)), help="0 땅 기준(기본), 1 metric")
    args = ap.parse_args()
    if args.build or args.rebuild:
        return build(args.rebuild)
    v = Viewer(args.start, args.scale)
    v.view = args.view
    if args.snapshot:
        cv2.imwrite(args.snapshot, v.render())
        return 0
    v.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
