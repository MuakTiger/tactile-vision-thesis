"""상대 깊이 모델로 거리 사진 120장 보기 (탐색).

Depth Anything V2 ViT-S 상대 모델(v1에서 쓰던 가중치, metric 미세조정 전)을
depth_viewer.py가 만든 캐시의 모델 입력(924x504, 장치 전처리와 같음)에 돌린다.
출력은 상대 역깊이(값이 클수록 가까움, 단위 없음, 사진마다 배율·이동이 다름).

세 가지로 본다.
  1. v1 방식: 사진마다 최솟값~최댓값을 0~1로 늘린 값(가까움 정도) → 7배 반올림 = 단계
  2. 땅 기준 m 환산: 카메라 높이 0.70 m·수평이면 화면 아래 땅의 거리를 계산할 수 있다
     (d = f·h / (y − y0)). 땅 줄의 상대값을 1/d에 직선으로 맞춰 상자의 상대값을 m로 바꾼다
  3. 비교: 실내 metric 모델 − 0.44 m (exp_distance.csv)

  python relative_depth.py --build   # 상대 모델 추론, 캐시에 <이름>_rel.npy 저장 (GPU)
  python relative_depth.py           # 분석·그림 (CPU)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from distance_analysis import RAW, OUT_CSV, OUT_DIR, SITES, load_rois, load_shots, roi_to_model, inner_slice

HERE = Path(__file__).resolve().parent
CACHE = HERE / "data" / "depth_cache"
OUT = OUT_DIR / "relative"
REL_REPO = Path.home() / "sensory_substitution" / "Depth-Anything-V2"
REL_CKPT = REL_REPO / "checkpoints" / "depth_anything_v2_vits.pth"
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

H_CAM = 0.70          # 렌즈 높이 (사용자, NOTES.md)
F_RAW = 908.0         # 원본 1280x720 초점거리 가정 (NOTES.md)
CY_RAW = 360.0        # 주점 = 원본 가운데 가정, 카메라 수평(역산 0.0~+0.2°)
GROUND_MAX_M = 3.5    # 이 거리 안쪽 땅 줄만 맞춤에 쓴다
B_INDOOR = -0.44      # 실내 사진으로 정한 더하기 보정
NEAR = 0.5


def level(d: float, far: float) -> int:
    """장치 log 매핑(필터 없음). d가 inf면 0."""
    if not math.isfinite(d) or d >= far:
        return 0
    if d <= NEAR:
        return 7
    return int(np.rint(7 * (math.log(far) - math.log(d)) / (math.log(far) - math.log(NEAR))))


def build() -> None:
    import torch
    sys.path.insert(0, str(REL_REPO))
    from depth_anything_v2.dpt import DepthAnythingV2

    model = DepthAnythingV2(encoder="vits", features=64, out_channels=[48, 96, 192, 384])
    model.load_state_dict(torch.load(REL_CKPT, map_location="cpu"))
    model = model.cuda().eval()
    mean = torch.tensor([0.485, 0.456, 0.406], device="cuda").view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device="cuda").view(3, 1, 1)
    n = 0
    for folder in SITES:
        for p in sorted((CACHE / folder).glob("*.npz")):
            img = np.load(p)["input_bgr"]
            t = torch.from_numpy(img[:, :, ::-1].copy()).cuda().permute(2, 0, 1).float().div_(255)
            t = ((t - mean) / std).unsqueeze(0)
            with torch.no_grad():
                rel = model(t)[0].float().cpu().numpy()
            assert rel.shape == img.shape[:2], rel.shape
            np.save(p.with_name(p.stem + "_rel.npy"), rel.astype(np.float16))
            n += 1
    print(f"상대 깊이 {n}장 저장 ({REL_CKPT.name}, fp32)")


def ground_fit(rel: np.ndarray, mb, crop) -> tuple[float, float, int]:
    """땅 줄의 상대값 중앙값을 1/d에 맞춘다: rel = A·(1/d) + B. (A, B, 쓴 줄 수)"""
    H, W = rel.shape
    _, cy, _, ch = crop
    f = F_RAW * H / ch
    y0 = (CY_RAW - cy) * H / ch
    y_top = int(math.ceil(y0 + f * H_CAM / GROUND_MAX_M))
    x, y, w, h = mb
    cols = np.ones(W, bool)
    cols[max(0, int(x - 0.5 * w)):min(W, int(x + 1.5 * w))] = False  # 상자·손수레 빼기
    ys, vals = [], []
    for r in range(y_top, H):
        use = cols if r >= y else np.ones(W, bool)
        if use.sum() < W * 0.2:
            continue
        ys.append(r)
        vals.append(float(np.median(rel[r, use])))
    q = (np.array(ys) - y0) / (f * H_CAM)
    v = np.array(vals)
    keep = np.ones(len(q), bool)
    for _ in range(2):  # 벗어난 줄 빼고 다시 맞춤
        A, B = np.polyfit(q[keep], v[keep], 1)
        res = v - (A * q + B)
        mad = np.median(np.abs(res[keep] - np.median(res[keep]))) + 1e-6
        keep = np.abs(res) <= 3 * 1.4826 * mad
    A, B = np.polyfit(q[keep], v[keep], 1)
    return float(A), float(B), int(keep.sum())


def analyze() -> list[dict]:
    rois = load_rois()
    metric = {}
    with OUT_CSV.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["model"] == "indoor":
                metric[(r["site"], r["file"])] = float(r["est_m"])
    rows = []
    for s in load_shots():
        key = (s["folder"], s["file"])
        if key not in rois:
            continue
        p = CACHE / s["folder"] / s["file"].replace(".png", ".npz")
        z = np.load(p)
        rel = np.load(p.with_name(p.stem + "_rel.npy")).astype(np.float32)
        crop = tuple(int(v) for v in z["crop"])
        mb = roi_to_model(rois[key], crop, (rel.shape[1], rel.shape[0]))
        rs, cs = inner_slice(mb, (rel.shape[1], rel.shape[0]))
        box = float(np.median(rel[rs, cs]))
        lo, hi = float(rel.min()), float(rel.max())
        close = (box - lo) / (hi - lo)
        A, B, ng = ground_fit(rel, mb, crop)
        d_g = A / (box - B) if box > B and A > 0 else float("inf")
        m = metric[(s["site"], s["file"])] + B_INDOOR
        rows.append({"env": s["env"], "site": s["site"], "file": s["file"], "true_m": s["true_m"],
                     "rel_box": box, "rel_min": lo, "rel_max": hi, "close_v1": close,
                     "step_v1": int(np.rint(7 * close)), "ground_A": A, "ground_B": B,
                     "ground_rows": ng, "ground_m": d_g, "metric_m": m})
    return rows


def spearman(a, b) -> float:
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def summarize(rows: list[dict]) -> str:
    out = []
    for env in ("indoor", "outdoor"):
        for site in ("site1", "site2"):
            rs = [r for r in rows if r["env"] == env and r["site"] == site]
            t = np.array([r["true_m"] for r in rs])
            out.append(f"\n## {env} {site} (n={len(rs)})")
            out.append(f"순위 상관(상대값 vs 1/거리): {spearman([r['rel_box'] for r in rs], 1 / t):.3f}")
            for name, k in (("땅 기준 m", "ground_m"), ("metric −0.44", "metric_m")):
                e = np.array([r[k] for r in rs])
                ok = np.isfinite(e)  # 땅 기준: 땅이 가려져 맞춤이 안 된 사진은 뺀다
                mape = np.mean(np.abs(e[ok] - t[ok]) / t[ok]) * 100
                out.append(f"{name}: MAPE {mape:.1f}%" + (f" (맞춤 실패 {(~ok).sum()}장 제외)" if (~ok).any() else ""))
            for d in sorted(set(t)):
                g = [r for r in rs if r["true_m"] == d]
                cl = np.array([r["close_v1"] for r in g])
                st = sorted(r["step_v1"] for r in g)
                gm = np.array([r["ground_m"] for r in g])
                mm = np.array([r["metric_m"] for r in g])
                out.append(f"  {d:g} m: v1 가까움 {cl.mean():.2f}±{cl.std():.2f} 단계 {st} | "
                           f"땅 기준 {np.median(gm):.2f} m | metric-0.44 {mm.mean():.2f} m")
    return "\n".join(out)


def sheet(rows: list[dict]) -> Path:
    """장소마다 거리별 한 장(03번): 입력 / 상대(v1 방식 정규화) / 실내 metric."""
    from PIL import Image, ImageDraw, ImageFont
    rois = load_rois()
    TW, TH, LAB = 308, 168, 34
    font = ImageFont.truetype(FONT, 17)
    by = {(r["site"], r["file"]): r for r in rows}
    blocks = []
    for folder in SITES:
        env, site = folder.split("_")[1], folder.split("_")[0]
        files = {}
        for r in rows:
            if r["env"] == env and r["site"] == site:
                files.setdefault(r["true_m"], []).append(r["file"])
        dists = sorted(files)
        canvas = np.zeros((LAB + 3 * TH + 3 * 22, TW * 6, 3), np.uint8)
        for i, d in enumerate(dists):
            fname = sorted(files[d])[min(2, len(files[d]) - 1)]
            p = CACHE / folder / fname.replace(".png", ".npz")
            z = np.load(p)
            rel = np.load(p.with_name(p.stem + "_rel.npy")).astype(np.float32)
            img = z["input_bgr"].copy()
            mb = roi_to_model(rois[(folder, fname)], tuple(int(v) for v in z["crop"]), (924, 504))
            x, y, w, h = (int(round(v)) for v in mb)
            reln = ((rel - rel.min()) / (rel.max() - rel.min()) * 255).astype(np.uint8)
            relc = cv2.applyColorMap(reln, cv2.COLORMAP_INFERNO)
            dm = np.clip(z["indoor_depth_m"] + B_INDOOR, NEAR, 8.0)
            met = cv2.applyColorMap(((np.log(8.0) - np.log(dm)) / (np.log(8.0) - np.log(NEAR)) * 255)
                                    .astype(np.uint8), cv2.COLORMAP_INFERNO)
            for j, im in enumerate((img, relc, met)):
                cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 3)
                y0 = LAB + j * (TH + 22)
                canvas[y0:y0 + TH, i * TW:(i + 1) * TW] = cv2.resize(im, (TW, TH), interpolation=cv2.INTER_AREA)
        pil = Image.fromarray(canvas[:, :, ::-1])
        dr = ImageDraw.Draw(pil)
        ko = {"indoor": "실내", "outdoor": "실외"}[env]
        dr.text((8, 7), f"{ko} {site[-1]}  — 위: 입력  가운데: 상대 깊이(사진마다 최소~최대, 밝을수록 가까움)  "
                        f"아래: 실내 metric-0.44 (0.5~8 m 로그)", font=font, fill=(255, 255, 255))
        for i, d in enumerate(dists):
            fname = sorted(files[d])[min(2, len(files[d]) - 1)]
            r = by[(site, fname)]
            gm = "∞" if not math.isfinite(r["ground_m"]) else f"{r['ground_m']:.1f}"
            for j, txt in enumerate((f"실제 {d:g} m",
                                     f"v1 가까움 {r['close_v1']:.2f} (단계 {r['step_v1']}) · 땅 기준 {gm} m",
                                     f"metric-0.44 {r['metric_m']:.2f} m")):
                dr.text((i * TW + 6, LAB + j * (TH + 22) + TH + 1), txt, font=font, fill=(255, 255, 255))
        blocks.append(np.array(pil)[:, :, ::-1])
    out = OUT / "relative_sheet.jpg"
    cv2.imwrite(str(out), np.vstack(blocks), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="상대 모델 추론 (GPU)")
    a = ap.parse_args()
    if a.build:
        build()
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    rows = analyze()
    with (OUT / "relative_rows.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    text = summarize(rows)
    (OUT / "relative_summary.md").write_text("# 상대 깊이 탐색 (자동 생성)\n" + text + "\n", encoding="utf-8")
    print(text)
    print("그림:", sheet(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
