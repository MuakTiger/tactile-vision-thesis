"""장치 코드(ground-scale 가지)로 거리 사진 120장을 다시 돌려 분석 결과와 맞는지 확인.

장치 쪽: ~/tactile-vision-ground 의 DepthEngine (TensorRT FP16)
  실내 엔진 + depth.indoor_offset_m, 실외 상대깊이 엔진 + GroundScaler(장치 설정 그대로, 사진마다 평활 초기화)
분석 쪽: out_distance/ground/ground_rows.csv (PyTorch FP32 상대깊이, ground_scale.py)
입력: depth_cache의 모델 입력(장치 전처리와 같음). 상자 값 = ROI 안쪽 60% 중앙값(분석과 같음).

  python device_ground_check.py      # GPU 사용 — 다른 모델 작업과 동시에 돌리지 말 것
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

from distance_analysis import OUT_DIR, SITES, inner_slice, load_rois, roi_to_model
from relative_depth import CACHE

DEVICE_REPO = Path.home() / "tactile-vision-ground"
OUT = OUT_DIR / "ground"


def main() -> int:
    sys.path.insert(0, str(DEVICE_REPO / "src"))
    from tactile_vision.config import load
    from tactile_vision.depth import DepthEngine
    from tactile_vision.ground import GroundScaler

    cfg = load(None)
    spec = cfg.depth.spec
    W, H = spec.width, spec.height
    indoor = DepthEngine(cfg.depth, cfg.grid, cfg.path(cfg.depth.engine), offset_m=cfg.depth.indoor_offset_m)
    rois = load_rois()
    ref = {}
    with (OUT / "ground_rows.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ref[(r["site"], r["file"])] = r
    rows, ground = [], None
    outdoor = None
    for folder in SITES:
        for p in sorted((CACHE / folder).glob("*.npz")):
            fname = p.stem + ".png"
            key = (folder, fname)
            if key not in rois:
                continue
            z = np.load(p)
            img, crop = z["input_bgr"], tuple(int(v) for v in z["crop"])
            if outdoor is None:
                ground = GroundScaler(cfg.ground, W, H, crop, cfg.camera.width)
                outdoor = DepthEngine(cfg.depth, cfg.grid, cfg.path(cfg.depth.outdoor_engine), ground=ground)
            rs, cs = inner_slice(roi_to_model(rois[key], crop, (W, H)), (W, H))
            indoor.infer(img)
            m = float(np.median(indoor.last_depth_map()[rs, cs]))
            outdoor.reset()  # 사진마다 독립 (평활 없이 그 사진의 배율)
            outdoor.infer(img)
            g = float(np.median(outdoor.last_depth_map()[rs, cs]))
            site = folder.split("_")[0]
            rr = ref[(site, fname)]
            rows.append({"env": rr["env"], "site": site, "file": fname, "true_m": float(rr["true_m"]),
                         "dev_metric_b": m, "ref_metric_b": float(rr["metric_b"]),
                         "dev_ground": g, "ref_ground": float(rr["ground"]), "dev_A": ground.raw,
                         "ref_A": float(rr["A"])})
    with (OUT / "device_check.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    L = [f"# 장치 코드 재현 확인 (`device_ground_check.py`, {DEVICE_REPO.name}, TensorRT FP16)", ""]
    for env in ("outdoor", "indoor"):
        for site in ("site1", "site2", None):
            rs_ = [r for r in rows if r["env"] == env and (site is None or r["site"] == site)]
            t = np.array([r["true_m"] for r in rs_])
            line = f"- {env} {site or '합침'} (n={len(rs_)}):"
            for k in ("ground", "metric_b"):
                d, a = np.array([r[f"dev_{k}"] for r in rs_]), np.array([r[f"ref_{k}"] for r in rs_])
                line += (f" {k} 장치 MAPE {np.mean(np.abs(d - t) / t) * 100:.1f}% / 분석 "
                         f"{np.mean(np.abs(a - t) / t) * 100:.1f}% (사진별 차 중앙 "
                         f"{np.median(np.abs(d - a) / a) * 100:.2f}%, 최대 {np.max(np.abs(d - a) / a) * 100:.1f}%);")
            L.append(line)
    text = "\n".join(L) + "\n"
    (OUT / "device_check.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
